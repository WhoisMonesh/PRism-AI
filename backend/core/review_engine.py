from typing import Optional, Union
from ..models import ReviewRequest, ReviewResult, PullRequestRef, Severity
from ..git_providers import get_git_provider
from ..agents import (
    ReviewAgent, DescribeAgent, ImproveAgent, SecurityAgent,
    ChangelogAgent, AskAgent, LabelsAgent, TestGenAgent,
    PerfAgent, SelfReviewAgent
)
from .policy_engine import PolicyEngine


class ReviewEngine:
    def __init__(self):
        self.policy_engine = PolicyEngine()

    async def execute_review(self, request: ReviewRequest) -> Union[ReviewResult, str]:
        pr = request.pr
        repo_full_name = f"{pr.owner}/{pr.repo}"

        if not self.policy_engine.is_tool_allowed(repo_full_name, request.tool):
            raise PermissionError(f"Tool '{request.tool}' not allowed for repo {repo_full_name}")

        provider = get_git_provider(pr.provider)
        diff = await provider.get_pr_diff(pr.owner, pr.repo, pr.number)
        files = await provider.get_pr_files(pr.owner, pr.repo, pr.number)

        filtered_files = self.policy_engine.filter_files(repo_full_name, files)

        if request.tool == "review":
            agent = ReviewAgent()
            result = await agent.run(diff, filtered_files)
            min_score = self.policy_engine.get_min_score(repo_full_name)
            result.approved = result.score >= min_score
            return result

        elif request.tool == "describe":
            agent = DescribeAgent()
            return await agent.run(diff, filtered_files)

        elif request.tool == "improve":
            agent = ImproveAgent()
            return await agent.run(diff, filtered_files)

        elif request.tool == "security":
            agent = SecurityAgent()
            return await agent.run(diff, filtered_files)

        elif request.tool == "changelog":
            agent = ChangelogAgent()
            return await agent.run(diff, filtered_files)

        elif request.tool == "ask":
            if not request.question:
                raise ValueError("Question required for 'ask' tool")
            agent = AskAgent()
            return await agent.run(diff, filtered_files, request.question)

        elif request.tool == "labels":
            agent = LabelsAgent()
            labels = await agent.run(diff, filtered_files)
            await provider.add_labels(pr.owner, pr.repo, pr.number, labels)
            return f"Added labels: {', '.join(labels)}"

        elif request.tool == "test_gen":
            agent = TestGenAgent()
            return await agent.run(diff, filtered_files)

        elif request.tool == "perf":
            agent = PerfAgent()
            return await agent.run(diff, filtered_files)

        elif request.tool == "self_review":
            agent = SelfReviewAgent()
            return await agent.run(diff, filtered_files)

        elif request.tool == "auto_issue":
            agent = ReviewAgent()
            result = await agent.run(diff, filtered_files)
            
            issues_created = []
            for comment in result.comments:
                if comment.severity in [Severity.CRITICAL, Severity.WARNING]:
                    title = f"AI {comment.category.value.capitalize()}: {comment.message[:50]}..."
                    body = f"### File: {comment.path}\n"
                    if comment.line:
                        body += f"### Line: {comment.line}\n"
                    body += f"\n**Category:** {comment.category.value}\n"
                    body += f"**Severity:** {comment.severity.value}\n\n"
                    body += f"**Description:**\n{comment.message}\n"
                    if comment.suggestion:
                        body += f"\n**AI Suggestion:**\n```\n{comment.suggestion}\n```"
                    
                    labels = ["ai-generated", f"severity-{comment.severity.value}", f"cat-{comment.category.value}"]
                    issue = await provider.create_issue(pr.owner, pr.repo, title, body, labels)
                    issues_created.append(issue.get("html_url", "unknown"))
            
            return {
                "status": "completed",
                "issues_created": issues_created,
                "summary": f"Created {len(issues_created)} issues from critical/warning findings."
            }

        else:
            raise ValueError(f"Unknown tool: {request.tool}")
