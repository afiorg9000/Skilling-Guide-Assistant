from openai import OpenAI
from config import Config
import time
from flask import current_app, session
import json
import os
import requests

class AssistantService:
    def __init__(self, session_id=None):
        api_key = 'sk-A6TiDIOFbTLAdROn4e4CcB2Y61bAm29adIIXbDGVTiT3BlbkFJZgQxw3f6wtsrTlq1Bt2nJ5w6D-FnuTCLvQu6-M3N4A'
        print(f"API Key: {api_key}")
        if not api_key:
            raise ValueError("OpenAI API key is not set.")
        
        self.openAI = OpenAI(api_key=api_key)

        self.assistant_name = 'ITG Skilling Guide'
        self.model_id = 'gpt-4-turbo'
        self.instruction = """
        You are a pre-sale assistant for ITG, responsible for helping users obtain certifications and skilling services. Your primary goal is to guide users through the process of enhancing their skills via ITG. 

        ### Responsibilities:
        1. **Onboarding**:
           - Identify if the user is a corporate representative or an individual.
           - Validate if the user has an account by asking for their email and using the appropriate API to check.

        2. **Needs Assessment**:
           - For corporate representatives:
             - Ask questions to understand:
               - Company size
               - Number of employees to be certified
               - Specific certification needs
           - For individuals:
             - Ask questions focused on:
               - Personal career goals
               - Interests

        3. **Personalized Recommendations**:
           - Map user responses to potential interests.
           - Recommend relevant categories or courses.
           - Offer dynamic suggestions based on user responses and behavior.

        4. **Course Database Utilization**:
           - Provide detailed information about:
             - Courses
             - Certifications
             - Pricing
             - Benefits

        5. **Career Endpoint Call**:
           - After gathering user goals and needs, call the career endpoint to retrieve:
             - Career name
             - Vendor suited for their goals
           - **Endpoint**: `https://itg.blockskill.co/t/sapi240620C`
           - **Payload**: 
             ```
             sec_key=p2zcm8@yarim80ezyn6b
             ```
           - **Content Type**: `application/x-www-form-urlencoded`
           - **Request Type**: `POST`

        6. **Recommendations Endpoint Call**:
           - Use the retrieved career name and vendor to call the following endpoint:
           - **Endpoint**: `https://itg.blockskill.co/t/sapi240725A`
           - **Payload**: 
             ```
             sec_key=p2zcm8@yarim80ezyn6b
             careerName=value
             vendor=value
             ```
           - **Content Type**: `application/x-www-form-urlencoded`
           - **Request Type**: `POST`

        ### Lead Qualification and Call to Action:
        - Provide a clear call to action for requesting a quote for both corporate and individual users.
        - Gather necessary user information and specific course details for the quote request.
        - **Quote Request Endpoint**: 
          - **Endpoint**: `https://itg.blockskill.co/t/sendAgentSelection240802`
          - **Payload**: 
            ```
            sec_key=p2zcm8@yarim80ezyn6b
            ```
          - **Data Structure**:
            ```json
            {
                "FirstName": "",
                "LastName": "",
                "email": "",
                "phone": "",
                "company": "",
                "country": "",
                "jobRole": "",
                "formname": "",
                "sendto": "",
                "selection": [
                    {
                        "sdate": "",
                        "cid": "",
                        "code": "",
                        "lang": "",
                        "qty": "",
                        "cname": "",
                        "chrs": "",
                        "vendor": "",
                        "edate": "",
                        "stime": "",
                        "etime": "",
                        "timezone": "",
                        "price": ""
                    }
                ]
            }
            ```
        - Ensure that all fields are included, even if they are left blank. Be cautious of special characters that might cause Unicode errors.
        """
        
        self.session_id = session_id
        self.assistant = self.get_or_create_assistant()
        self.thread = self.get_or_create_thread()

    def get_or_create_assistant(self):
        if 'assistant_id' in session:
            try:
                return self.openAI.beta.assistants.retrieve(session['assistant_id'])
            except Exception:
                assistant = self.create_assistant()
                session['assistant_id'] = assistant.id
                return assistant
        
        assistant = self.create_assistant()
        session['assistant_id'] = assistant.id
        return assistant

    def get_or_create_thread(self):
        if 'thread_id' in session:
            return self.openAI.beta.threads.retrieve(session['thread_id'])
        else:
            thread = self.create_thread()
            session['thread_id'] = thread.id
            return thread

    def define_function__validate_account(self):
        function = {
            "type": "function",
            "function": {
                "name": "validateAccount",
                "description": "Validate an account using email and security key.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sec_key": {"type": "string", "description": "Security key"},
                        "email": {"type": "string", "description": "Email to validate"}
                    },
                    "required": ["sec_key", "email"]
                }
            }
        }
        return function
    
    def define_function__get_student_courses(self):
        function = {
            "type": "function",
            "function": {
                "name": "getStudentCourses",
                "description": "Retrieve courses for a student by ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sec_key": {"type": "string", "description": "Security key"},
                        "ID": {"type": "string", "description": "Student ID"}
                    },
                    "required": ["sec_key", "ID"]
                }
            }
        }
        return function

    def define_function__get_career(self):
        function = {
            "type": "function",
            "function": {
                "name": "getCareer",
                "description": "Retrieve career information based on security key.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sec_key": {"type": "string", "description": "Security key"}
                    },
                    "required": ["sec_key"]
                }
            }
        }
        return function

    def define_function__get_course_database(self):
        function = {
            "type": "function",
            "function": {
                "name": "getCourseDatabase",
                "description": "Retrieve course database using career name and vendor.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sec_key": {"type": "string", "description": "Security key"},
                        "careerName": {"type": "string", "description": "Career name"},
                        "vendor": {"type": "string", "description": "Vendor name"}
                    },
                    "required": ["sec_key", "careerName", "vendor"]
                }
            }
        }
        return function

    def define_function__request_quote(self):
        function = {
            "type": "function",
            "function": {
                "name": "requestQuote",
                "description": "Submit a quote request with user and course details.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sec_key": {"type": "string", "description": "Security key"},
                        "data": {"type": "string", "description": "User and course selection details in JSON format"}
                    },
                    "required": ["sec_key", "data"]
                }
            }
        }
        return function

    def create_assistant(self):
        return self.openAI.beta.assistants.create(
            name=self.assistant_name,
            instructions=self.instruction,
            model=self.model_id,
            tools=[
                self.define_function__validate_account(),
                self.define_function__get_student_courses(),
                self.define_function__get_career(),
                self.define_function__get_course_database(),
                self.define_function__request_quote()
            ]
        )

    def create_thread(self):
        return self.openAI.beta.threads.create()
    
    def generate_tool_outputs(self, tool_calls):
        tool_outputs = []

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = tool_call.function.arguments
            tool_call_id = tool_call.id
            args_dict = json.loads(arguments)

            if function_name == 'validateAccount':
                output = validate_account2(args_dict['email'])
                tool_outputs.append({
                    "tool_call_id": tool_call_id,
                    "output": output,
                })
            elif function_name == 'getStudentCourses':
                output = get_student_courses2(args_dict['ID'])
                tool_outputs.append({
                    "tool_call_id": tool_call_id,
                    "output": output,
                })
            elif function_name == 'getCareer':
                output = get_career2()
                tool_outputs.append({
                    "tool_call_id": tool_call_id,
                    "output": output,
                })
            elif function_name == 'getCourseDatabase':
                output = get_course_database2(args_dict['careerName'], args_dict['vendor'])
                tool_outputs.append({
                    "tool_call_id": tool_call_id,
                    "output": output,
                })
            elif function_name == 'requestQuote':
                output = request_quote2(args_dict['data'])
                tool_outputs.append({
                    "tool_call_id": tool_call_id,
                    "output": output,
                })

        return tool_outputs

    def run_assistant(self, message):
        current_app.logger.info(f'Running assistant: {message}')
        message = self.add_message_to_thread("user", message)
        action_response = None

        try:
            run = self.openAI.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
            )
            run = self.wait_for_update(run)

            if run.status == "failed":
                current_app.logger.error(f'Run failed. Full run object: {json.dumps(run.model_dump(), indent=2)}')
                return f"Assistant run failed: {run.last_error.message if run.last_error else 'Unknown error'}"
            elif run.status == "requires_action":
                current_app.logger.info(f'Run requires action: {run}')
                action_response = self.handle_require_action(run)
            else:
                current_app.logger.info('Run completed')
                action_response = self.get_last_assistant_message()

            return action_response
        except Exception as e:
            current_app.logger.error(f'Error running assistant: {str(e)}')
            return f"An error occurred: {str(e)}"

    def wait_for_update(self, run, timeout=60):
        start_time = time.time()
        while run.status == "queued" or run.status == "in_progress":
            if time.time() - start_time > timeout:
                current_app.logger.error(f'Run timed out after {timeout} seconds')
                return run
            run = self.openAI.beta.threads.runs.retrieve(
                thread_id=self.thread.id,
                run_id=run.id,
            )
            time.sleep(1)
            current_app.logger.info(f'Run status: {run.status}')

        current_app.logger.info(f'Final run status: {run.status}')
        return run
    
    def add_message_to_thread(self, role, message):
        current_app.logger.info(f'Adding message to thread: {role}, {message}')
        return self.openAI.beta.threads.messages.create(
            thread_id=self.thread.id,
            role=role,
            content=message,
        )
    
    def get_last_assistant_message(self):
        intLog('in get_last_assistant_message')
        current_app.logger.info('Getting last assistant message')
        messages = self.openAI.beta.threads.messages.list(thread_id=self.thread.id)
        if messages.data[0].role == 'assistant':
            message = messages.data[0]
            for content_block in message.content:
                if content_block.type == 'text':
                    return content_block.text.value
        else:
            return None
    
    def handle_require_action(self, run):
        current_app.logger.info('Handling required action')
        tool_calls = run.required_action.submit_tool_outputs.tool_calls
        current_app.logger.info(f'Tool calls: {tool_calls}')
        
        tool_outputs = self.generate_tool_outputs(tool_calls)

        run = self.openAI.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread.id,
            run_id=run.id,
            tool_outputs=tool_outputs
        )
        
        run = self.wait_for_update(run)

        if run.status == "failed":
            current_app.logger.error('Run failed')
            return Noneß
        elif run.status == "completed":
            return self.get_last_assistant_message()

# outside functions
def intLog(dta):
    with open("runtime.log", "a") as f:
        f.write(' '+str(dta)+'\n')
    return 'ok'

def validate_account2(email):
    intLog('in validate_account: ' + str(email))
    url = "https://itg.blockskill.co/t/sapi240722A"
    payload = {
        'sec_key': 'p2zcm8@yarim80ezyn6b',
        'email': email
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    response = requests.post(url, data=payload, headers=headers)

    intLog('response: ' + str(response.text))
    return response.text

def get_student_courses2(student_id):
    intLog('in get_student_courses: ' + str(student_id))
    url = "https://itg.blockskill.co/t/sapi240620B"
    payload = {
        'sec_key': 'p2zcm8@yarim80ezyn6b',
        'ID': student_id
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    response = requests.post(url, data=payload, headers=headers)

    intLog('response: ' + str(response.text))
    return response.text

def get_career2():
    intLog('in get_career')
    url = "https://itg.blockskill.co/t/sapi240620C"
    payload = {'sec_key': 'p2zcm8@yarim80ezyn6b'}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    response = requests.post(url, data=payload, headers=headers)

    intLog('response: ' + str(response.text))
    return response.text

def get_course_database2(career_name, vendor):
    intLog('in get_course_database: ' + str(career_name) + ', ' + str(vendor))
    url = "https://itg.blockskill.co/t/sapi240725A"
    payload = {
        'sec_key': 'p2zcm8@yarim80ezyn6b',
        'careerName': career_name,
        'vendor': vendor
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    response = requests.post(url, data=payload, headers=headers)

    intLog('response: ' + str(response.text))
    return response.text

def request_quote2(data):
    intLog('in request_quote: ' + str(data))
    url = "https://itg.blockskill.co/t/sendAgentSelection240802"
    payload = {
        'sec_key': 'p2zcm8@yarim80ezyn6b',
        'data': data
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    response = requests.post(url, data=payload, headers=headers)

    intLog('response: ' + str(response.text))
    return response.text
