from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    HumanMessage,
    SystemMessage,
)


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
        self.reset()

    def reset(self):
        self.message_history = ["Following is the conversation so far (if any)."]

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
            model: ChatOpenAI,
            plan: dict,
    ) -> None:
        super().__init__(name, "", model)
        self.plan = plan
        self.generate_persona()
        self.system_message = SystemMessage(content=self.generate_interview_system_message)

    def generate_persona(self):
        persona = f''' 
        Your role and persona is described deblow:
        Your name is {self.name}
        You are an intelligent, sensitive and polite interviewer.
        You have done several interviewing on topics regarding technology, AI, and startups.
        
        '''
        return persona

    @property
    def generate_interview_system_message(self):
        prompt = f'''
        Your goal is conducting an interview for {self.plan["purpose"].lower()}
        The background of this interview is: {self.plan["background"].lower()}
        The target audience are: {self.plan["target_audience"].lower()}
        '''

        if self.plan["questions in order"]:
            prompt += "Please conduct the interview with the following suggested questions in order as the plan: " + "\n"
        else:
            prompt += "Please conduct the interview with the following suggested questions with the most ideal and smooth order as the plan: " + "\n"
        for i, q in enumerate(self.plan["questions"]):
            prompt += str(i + 1) + ". " + self.plan["questions"][i] + "\n"

        prompt += '''
        Instructions:
        - If the conversation has not started yet, please welcome the interviewee and introduce the purpose of this interview, and then ask the first suggested question.
        
        '''
        if self.plan["follow-up questions"]:
            prompt += "- If it is helpful, relevant, and appropriate to the purpose, you may ask a follow-up questions nicely instead." + "\n" + "\n"

        prompt += '''
        - If the last question was not answered properly or sufficiently from the interviewee or if the interviewee appears confused, please ask the question again with some appropriate paraphrasing.
        '''

        prompt += '''
        - If according to the suggested questions and plan, it is determined that you have completed the interview please thanks the interviewee and give the interviewee a summary with less than 200 words for the interview.
        '''

        prompt += "DO ask questions one by one. \n"
        prompt += "DO only complete your current single turn. \n"
        return prompt


def generate_single_interview_response(name, plan, conversation):
    interviewing_agent = InterviewAgent(name=name,
                                        model=ChatOpenAI(
                                            model_name='gpt-3.5-turbo',
                                            temperature=0.5),
                                        plan=plan,
                                        )
    for utterance in conversation:
        if utterance != "" and utterance["message"]:
            interviewing_agent.receive(utterance["speaker"], utterance["message"])

    agent_response, signal_completion = interviewing_agent.send()
    return agent_response, signal_completion
