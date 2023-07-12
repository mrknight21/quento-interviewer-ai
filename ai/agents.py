from langchain import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    HumanMessage,
    SystemMessage,
)

from ai.utilities import parsing_response

MAX_TRYOUT = 3

class QuentoResponse(BaseModel):
    action_type: str = Field(description="the selected action type for the response")
    response: str = Field(description="the text of the response")


class DialogueAgent:
    def __init__(
            self,
            name: str,
            system_message: SystemMessage,
            model: ChatOpenAI,
    ) -> None:
        self.name = name
        self.system_message = system_message
        self.model = model
        self.prefix = f"{self.name}: "
        self.parser = PydanticOutputParser(pydantic_object=QuentoResponse)
        self.reset()

    def reset(self):
        self.message_history = []

    def send(self) -> str:
        """
        Applies the chatmodel to the message history
        and returns the message string
        """
        signal_quit = False
        message = self.model(
            [
                self.system_message,
                HumanMessage(content="\n".join(self.message_history + [self.prefix])),
            ]
        )
        return message.content, signal_quit

    def receive(self, name: str, message: str) -> None:
        """
        Concatenates {message} spoken by {name} into message history
        """
        self.message_history.append(f"{name}: {message}")


class HumanAgent(DialogueAgent):
    def __init__(
            self,
            name: str,
    ) -> None:
        super().__init__(name, "", None)

    def send(self) -> str:
        """
        Applies the chatmodel to the message history
        and returns the message string
        """

        human_response = input()
        signal_quit = human_response == "quit"

        return human_response, signal_quit


class InterviewAgent(DialogueAgent):
    def __init__(
            self,
            name: str,
            model: OpenAI,
            plan: dict,
    ) -> None:
        super().__init__(name, "", model)
        self.plan = plan
        self.promptTemplate = self.generate_interview_system_message()
        # self.system_message = SystemMessage(content=self.generate_interview_system_message)

    def generate_interview_system_message(self):
        template = """/
        Your role and persona is described deblow:
        Your name is {name}. You are an intelligent, sensitive and polite interviewer.
        You have done several interviewing on topics regarding technology, AI, and startups.
        
        Your current goal is conducting an interview for {purpose}.
        The background of this interview is: {background}.
        The target audience are: {target_audience}.
        
        Please conduct the interview with the following suggested questions with the most ideal and smooth order as the plan: 
        {questions}
        
        Given the current dialogue history(this part would be empty, if the dialogue has not started yet):
        {history}
        
        First please choose one of the action type from below:
        "#NEXTQUESTION": If the previous question or task has been completed, please move on to the next question.
        "#STARTING": If the conversation has not started yet, please welcome the interviewee and introduce the purpose of this interview, and then ask the first suggested question.
        "#FOLLOWUPQUESTION": If it is helpful, relevant, and appropriate to the purpose, you may ask a follow-up questions nicely instead.
        "#ASKAGAIN": If the last question was not answered properly or sufficiently from the interviewee or if the interviewee appears confused, please ask the question again with some appropriate paraphrasing.
        "#COMPLETING" If according to the suggested questions and plan, it is determined that you have completed the interview please thanks the interviewee and give the interviewee a summary with less than 200 words about the interview.
        
        Notice:
        - DO only ask one question at once.
        - DO only complete your current single turn.
        - DO generate the output response based on the selected action type from above
        
        --------

        Put the final output message, including the action_type and response, in the format
        
        "action_type": ".."
        "response": ".."
        
        for example:
        "action_type": "#NEXTQUESTION"
        "response": "What are the common challenges or pain points faced by startups during the problem validation phase?"
        
        """

        prompt = PromptTemplate(
            input_variables=["name", "purpose", "background", "target_audience", "questions", "history"],
            template=template,
        )

        return prompt

    def send(self) -> str:
        """
        Applies the chatmodel to the message history
        and returns the message string
        """
        signal_quit = False
        response = None

        questions = "\n".join(self.plan["questions"])
        history = "\n".join(self.message_history)
        _input = self.promptTemplate.format_prompt(name=self.name,
                                                   purpose=self.plan["purpose"],
                                                   background=self.plan["background"],
                                                   target_audience=self.plan["target_audience"],
                                                   questions=questions,
                                                   history=history)
        for i in range(MAX_TRYOUT):
            output = self.model(_input.to_string())
            result = parsing_response(output)
            if result:
                response = result["response"]
                action_type = result["action_type"]
                if action_type == "#COMPLETING":
                    signal_quit = True
                break
        return response, signal_quit


def generate_single_interview_response(name, plan, conversation):
    interviewing_agent = InterviewAgent(name=name,
                                        model=OpenAI(
                                            model_name='gpt-3.5-turbo',
                                            temperature=0.5),
                                        plan=plan,
                                        )
    for utterance in conversation:
        if utterance != "" and utterance["message"]:
            interviewing_agent.receive(utterance["speaker"], utterance["message"])

    agent_response, signal_completion = interviewing_agent.send()
    return agent_response, signal_completion
