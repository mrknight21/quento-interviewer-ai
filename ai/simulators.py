from typing import List, Callable
from ai.agents import InterviewAgent, HumanAgent, DialogueAgent
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI

class DialogueSimulator:
    def __init__(
            self,
            agents: List[DialogueAgent],
            selection_function: Callable[[int, List[DialogueAgent]], int],
    ) -> None:
        self.agents = agents
        self._step = 0
        self.select_next_speaker = selection_function
        self.max_iters = 20

    def reset(self):
        self._step = 0
        for agent in self.agents:
            agent.reset()

    def inject(self, name: str, message: str):
        """
        Initiates the conversation with a {message} from {name}
        """
        for agent in self.agents:
            agent.receive(name, message)

        # increment time
        self._step += 1

    def step(self) -> tuple[str, str]:
        termination = False

        # 1. choose the next speaker
        speaker_idx = self.select_next_speaker(self._step, self.agents)
        speaker = self.agents[speaker_idx]

        # 2. next speaker sends message
        message, signal_termination = speaker.send()
        termination = signal_termination

        # 3. everyone receives message
        for receiver in self.agents:
            receiver.receive(speaker.name, message)

        # 4. increment time
        self._step += 1

        if self._step == self.max_iters:
            termination = True

        return speaker.name, message, termination



from ai.utilities import select_next_speaker
import os
import openai
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file
openai.api_key = os.environ['OPENAI_API_KEY']


def main():
    interview_plan = {
        "purpose": "Validating the need of large scale automatic interviewing and knowledge ecilitatioin using AI.",
        "background": '''Our startup aims to revolutionize the interview process by harnessing the power of AI. We strive to automate knowledge elicitation and information collection, enabling scalable and accurate insights. By replacing traditional, human-dependent interviewing methods, our solution empowers industries such as media, research, and beyond to gather comprehensive data with larger sample sizes, leading to more reliable and profound outcomes.''',
        "questions": [
            "Can you describe the typical problem validation process that startups go through in your experience?",
            "What are the common challenges or pain points faced by startups during the problem validation phase?",
            "How do startups typically gather data and insights during the problem validation process? Is it a time-consuming or resource-intensive task?",
            "Do they conduct interview or any sorts of interactive approach to validate their problems?",
            "Do you think an AI-powered interview solution could potentially provide value in helping startups validate their problems more efficiently and effectively?",
            "What features or functionalities would you consider important in an AI-powered tool designed for problem validation in startups?",
            "Are there any concerns or potential drawbacks you foresee with using AI in the problem validation process for startups?"],
        "target_audience": "Startup investors who could potentially use the interview AI to help their starup founders validating their problems.",
        "time_limit": 20,
        "follow-up questions": True,
        "questions in order": True
    }

    agents = [InterviewAgent(name="Cojo",
                             model=OpenAI(
                                 model_name='gpt-3.5-turbo',
                                 temperature=0.2),
                             plan=interview_plan,
                             ),
              HumanAgent("Bryan Chen")]

    simulator = DialogueSimulator(
        agents=agents,
        selection_function=select_next_speaker
    )
    simulator.reset()
    # simulator.inject('Moderator', specified_topic)
    # print(f"(Moderator): {specified_topic}")
    # print('\n')

    while simulator._step < simulator.max_iters:
        name, message, termination = simulator.step()
        print(f"({name}): {message}")
        print('\n')

        if termination:
            break


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()