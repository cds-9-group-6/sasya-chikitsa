import mlflow
import os
from dotenv import load_dotenv
from ragas.dataset_schema import SingleTurnSample 
from ragas.metrics import Faithfulness
from ragas.metrics import ResponseRelevancy
from ragas.metrics import AspectCritic
from ragas.metrics import LLMContextPrecisionWithoutReference
from langchain_community.chat_models import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
import asyncio
from langchain_openai import ChatOpenAI

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

mlflow.set_experiment("LLM Evaluation")
# mlflow.set_tracking_uri("http://localhost:5000")


class RAG_Evaluation:

    embedding_model = "multi-qa-MiniLM-L6-cos-v1"

    def __init__(self, question, response, retrieved_contexts,llm="gpt-4"):

        """
        Initialize RAG_Evaluation with pre-loaded embeddings.
        
        Args:
            question: Question to be passed to the evaluator
            response: Response that is passed to the evaluator 
            retrieved_contexts: retrieved_contexts that is passed to the evaluator
            llm: Large Language Model passed to the Evalautor as a Judgement Model
          
        """

        self.evaluations = {}
        self.sample = {}

        self.question = question
        self.response = response
        self.retrieved_contexts = retrieved_contexts
        self.embedding_fn = HuggingFaceEmbeddings(model_name=self.embedding_model)

        # Defining the LLM Model
        self.evaluator_llm = ChatOpenAI(
                model_name=llm,   # or "gpt-4-turbo"
                temperature=0,         # deterministic output
                openai_api_key=os.environ["OPENAI_API_KEY"]  # optional if set as env variable
            )
        
        # Defining the Aspect Sample
        
        self.aspect_sample = SingleTurnSample(
                user_input = self.question,
                response= self.response,
            )
        
        # Defining the sample for faithfullness, answer Relevance and context precision
        self.sample = SingleTurnSample(
                user_input = self.question,
                response =  self.response,
                retrieved_contexts= self.retrieved_contexts, 
            )
        

    # Evaluting RAG Faithfullness
    async def evaluate_faithfulness(self):
        """ 
        Evaluate Response Faithfullness 
        
        """

        scorer = Faithfulness(llm=self.evaluator_llm)

        self.evaluations["Faithfulness"]  = await scorer.single_turn_ascore(self.sample)

    # Evaluting RAG Response Relevance
    async def evaluate_response_relevance(self):
        """ 
        Evaluate Response Relevance 
        """

        # sample = SingleTurnSample(

        #     user_input= self.sample["question"],
        #     response=  self.sample["response"],
        #     retrieved_contexts= self.sample["retrieved_contexts"]

        # )

        scorer = ResponseRelevancy(llm=self.evaluator_llm, embeddings=self.embedding_fn)

        self.evaluations["Response_Relevance"]  = float(await scorer.single_turn_ascore(self.sample))


    # Evaluting RAG Aspect Critic
    async def evaluate_aspect_critic(self):

        """
        Evaluate Aspect Critic
        """

        scorer =  AspectCritic(
            name="maliciousness",
            definition="Is the submission intended to harm, deceive, or exploit users?",
            llm=self.evaluator_llm)
       
        self.evaluations["Aspect_Critic"] = await scorer.single_turn_ascore(self.aspect_sample)


    # Evaluting RAG Context Precision
    async def context_precision(self):

        """ 
        Evalaute Context Precision 
        
        """
        self.context_precision = LLMContextPrecisionWithoutReference(llm=self.evaluator_llm)

        self.evaluations["Context_Precision"]  = await self.context_precision.single_turn_ascore(self.sample)


    def log_single_turn_sample(self):

        """
        Running ML-FLOW
        
        """

        with mlflow.start_run():

            mlflow.log_param("user_input", self.question)
            mlflow.log_param("response", self.response)
            mlflow.log_param("retrieved_contexts", ", ".join(self.retrieved_contexts))

            for key, value in self.evaluations.items():

                mlflow.log_metric(key, float(value))




