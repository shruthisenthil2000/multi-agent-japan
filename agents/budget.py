from __future__ import annotations

from agents.base import AgentContext, AgentResult, BaseAgent
from agents.runner import _compact_json, run_json_agent
from llm.schemas import BudgetCategory, BudgetPlan, LogisticsPlan, Money, TravelBrief


def normalize_budget(plan: BudgetPlan) -> BudgetPlan:
    """Scale category amounts to match total within validator tolerance."""
    total = plan.total.amount
    cat_sum = sum(c.amount for c in plan.categories)
    if cat_sum <= 0:
        return plan
    amounts = [c.amount for c in plan.categories]
    if abs(cat_sum - total) > total * 0.02:
        ratio = total / cat_sum
        amounts = [round(a * ratio, 2) for a in amounts]
        drift = round(total - sum(amounts), 2)
        if amounts:
            amounts[-1] = round(amounts[-1] + drift, 2)
    categories = [
        BudgetCategory(
            name=c.name,
            amount=amt,
            percent=round(amt / total * 100, 1) if total else 0,
        )
        for c, amt in zip(plan.categories, amounts)
    ]
    return plan.model_copy(update={"categories": categories})


class BudgetAgent(BaseAgent):
    name = "budget"

    async def arun(self, ctx: AgentContext, **kwargs) -> AgentResult:
        brief = TravelBrief.model_validate(ctx.travel_brief)
        logistics = ctx.get_artifact("logistics") or {}
        user = (
            f"TravelBrief:\n{_compact_json(brief.model_dump(mode='json'))}\n\n"
            f"LogisticsPlan:\n{_compact_json(logistics)}"
        )
        model, result = await run_json_agent(
            self.name,
            ctx,
            BudgetPlan,
            user,
            keep_budget_typical=True,
            **kwargs,
        )
        try:
            normalized = normalize_budget(model)
        except ValueError:
            normalized = normalize_budget(
                BudgetPlan(
                    schema_version="1.0",
                    total=Money(
                        amount=brief.budget.amount,
                        currency=brief.budget.currency,
                    ),
                    categories=model.categories,
                    tradeoffs=model.tradeoffs,
                    warnings=model.warnings,
                )
            )
        result.payload = normalized.model_dump(mode="json")
        return result
