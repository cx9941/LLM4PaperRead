from crewai import Agent, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Optional
from tools.custom_llm import executor_llm
from source.custom_crew import Custom_Crew
from pathlib import Path

@CrewBase
class PaperRead():
    def __init__(self, configs):
        self.output_log_file = configs['output_log_file']
        self.report_file = configs['report_file']
        super().__init__()


    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            llm=executor_llm,
            verbose=True
        )

    @agent
    def reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config['reviewer'],
            llm=executor_llm,
            verbose=True
        )

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_analyst'],
            llm=executor_llm,
            verbose=True
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'],
            agent=self.researcher()
        )

    @task
    def review_task(self) -> Task:
        return Task(
            config=self.tasks_config['review_task'],
            agent=self.reviewer()
        )

    @task
    def reporting_task(self) -> Task:
        # Ensure directory exists
        output_dir = Path(self.report_file).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return Task(
            config=self.tasks_config['reporting_task'],
            agent=self.reporting_analyst(),
            output_file=self.report_file
        )

    @crew
    def crew(self) -> Custom_Crew:
        # Get log file path from inputs or use default
        output_log_file = self.output_log_file
        
        # Ensure directory exists
        log_dir = Path(output_log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        return Custom_Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            output_log_file=output_log_file,
        )