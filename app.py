import streamlit as st
import os
import replicate
from time import sleep
import json


st.title("Fitting Room Assistant 👗")

#---------------------------------------------------- Object Classes ----------------------------------------------------
class Llama2():
    def __init__(self):
        #--- Settings
        self.temperature = 0.1
        self.top_p = 0.9
        self.max_length = 256

        #--- Models
        self.llm_7b = "a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea"
        self.llm_13b = "a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5"

        #--- Instructions
        self.instructions = [
            "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'.",
            "As an Assistant, you never shows the previous answers from the User in the prompt.",
            "You should always match the user request with one of the following topics:'casual', 'party', 'sport', 'formal', 'travelling'. and answer accordingly.",
            "You only answer requests related to fashion and clothes. If the topic is not this, answer: 'I'm not trained with data not related to fashion and clothes.'",
        ]

    def generate_llama2_response(self, prompt_input, model = "llm_13b"):
        #--- Select model
        if model == "llm_13b": model = self.llm_13b
        if model == "llm_7b": model = self.llm_7b
        
        #--- Add initial instructions
        for instruction in self.instructions:
            string_dialogue = instruction + "\n\n"

        #--- Add the dialogue history
        for dict_message in st.session_state.messages:
            if dict_message["role"] == "user":
                string_dialogue += "User: " + dict_message["content"] + "\n\n"
            else:
                string_dialogue += "Assistant: " + dict_message["content"] + "\n\n"
        
        #--- Run the model
        output = replicate.run(model, 
                            input={"prompt": f"{string_dialogue} {prompt_input} Assistant: "})
        return output

    def give_profile_overview(self, request):
        #--- Give an overview of the user profile and the best university, and why it is the best match
        overview_profile = f"Based on my request, what outfit is better for me: 'casual', 'party', 'sport', 'formal', 'travel'"

        final_prompt = request + " | " + overview_profile

        return self.generate_llama2_response(final_prompt)

class Assistant():
    def __init__(self):
        self.messages = []
        self.role = "assistant"
        self.unimatch_questions = {
            1: "Tell me a little bit more about your hobbies!",
            2: "What fields in the school are you interested in?",
            3: "What is your budget for studying?"
        }
        self.unimatch_on = False
        self.unibuddy_on = False
        self.last_user_reply = ""
        self.user_replies_counter = 0
            

    def print_and_add_message(self, content):
        sleep(0.5)
        #--- Print message
        with st.chat_message(self.role):
            st.markdown(content)

        #--- Add to history
        self.messages.append({"role": self.role, "content": content})
        st.session_state.messages.append({"role": self.role, "content": content})
    
    def unimatch_question(self):
        self.print_and_add_message(self.unimatch_questions[self.user_replies_counter])

    def set_unimatch_on(self, value):
        self.unimatch_on = value
    def set_unibuddy_on(self, value):
        self.unibuddy_on = value
    def set_last_user_reply(self, value):
        self.last_user_reply = value
    def update_user_replies_counter(self):
        #--- load the json file
        with open("cache-data.json") as f:
            data = json.load(f)

        #--- update the user_replies_counter
        self.user_replies_counter = data["user_replies_counter"]
        self.user_replies_counter += 1

        #--- update the json file
        data["user_replies_counter"] = self.user_replies_counter
        with open("cache-data.json", "w") as f:
            json.dump(data, f)

    def check_finished_questions(self):
        #--- get matching_done from the cache
        with open("cache-data.json") as f:
            data = json.load(f)
        matching_done = data["matching_done"]
        if self.user_replies_counter > len(self.unimatch_questions) and matching_done == False:
            self.print_and_add_message("Great! I have all the information I need. Let me find the best university for you! 🎓")
            self.unimatch_on = False
            self.user_replies_counter = 0
            #--- update the json file
            with open("cache-data.json") as f:
                data = json.load(f)
            data["user_replies_counter"] = self.user_replies_counter
            with open("cache-data.json", "w") as f:
                json.dump(data, f)
            return True

    def get_last_user_reply(self):
        return self.last_user_reply

class User():
    def __init__(self):
        self.messages = []
        self.role = "user"

    def print_and_add_message(self, content):
        sleep(0.5)
        #--- Print message
        with st.chat_message(self.role):
            st.markdown(content)

        #--- Add to history
        self.messages.append({"role": self.role, "content": content})
        st.session_state.messages.append({"role": self.role, "content": content})

    def update_user_profile(self):
        #--- load the json file
        with open("cache-data.json") as f:
            data = json.load(f)
        data["user_profile"] = data["user_profile"] + self.messages[-1]["content"] + " | "

        #--- update the json file
        with open("cache-data.json", "w") as f:
            json.dump(data, f)

    
    def get_last_reply(self):
        return self.messages[-1]["content"]


def image_matcher(text_input):
    #--- Counting which key-words appears the most in the input
    fashion_styles = ["casual", "party", "sport", "formal", "travel"]

    #--- Counting the number of times each key-word appears in the input
    count_dict = {}
    for style in fashion_styles:
        count_dict[style] = text_input.count(style)
    
    #--- Getting the key-word with the highest count
    max_key = max(count_dict, key=count_dict.get)

    #--- Returning the image that matches the key-word
    return max_key


# ------------------------------------ Initial Messages ------------------------------------
with st.chat_message("assistant"):
    st.markdown("Hey there 👋!")
    st.markdown("I'm here to help you to find the best outfit match for you! 🎉")
    st.markdown("Please, tell me what are you looking for today? 🤔")


#--------------------------------------- Settings ---------------------------------------
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# API settings
replicate_api = st.secrets['REPLICATE_API_TOKEN']
os.environ['REPLICATE_API_TOKEN'] = replicate_api

#--- Initialize Agents
assistant = Assistant()
user = User()
llama2 = Llama2()

#--- Image Address
image_address = {
    "casual": "casual.jpeg",
    "party": "party.jpeg",
    "sport": "sport.jpeg",
    "formal": "formal.jpeg",
    "travel": "travelling.jpeg"
}

#=======================================================
# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
#=======================================================

if prompt := st.chat_input("What is up?"):
    user.print_and_add_message(prompt)

    # Display assistant response in chat message container
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):

                #====================================================
                #response = llama2.generate_llama2_response(prompt)
                #====================================================

                #====================================================
                response = llama2.give_profile_overview(prompt)
                #====================================================

                #====================================================
                placeholder = st.empty()
                full_response = ''
                for item in response:
                    full_response += item
                    placeholder.markdown(full_response)
                placeholder.markdown(full_response)
                #====================================================


                #------------------ PLOTTING IMAGES ------------------
                image_style_request = image_matcher(full_response)
                image_path = image_address[image_style_request]
                st.image(image_path, use_column_width=True)


        message = {"role": "assistant", "content": full_response}
        st.session_state.messages.append(message)