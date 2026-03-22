"""
Pipeline stage definitions and transition rules.

Each stage has a set of valid next stages, ensuring the state machine
only moves forward through the defined workflow.
"""

from mcp.models.rca_models import PipelineStage

STAGE_TRANSITIONS = {
    PipelineStage.INTAKE: [PipelineStage.EVIDENCE_CAPTURE, PipelineStage.FAILED],
    PipelineStage.EVIDENCE_CAPTURE: [PipelineStage.SUMMARIZATION, PipelineStage.FAILED],
    PipelineStage.SUMMARIZATION: [PipelineStage.TESTRAIL_MATCH, PipelineStage.FAILED],
    PipelineStage.TESTRAIL_MATCH: [
        PipelineStage.TEST_GENERATION,
        PipelineStage.BLAST_RADIUS,  # Skip to blast radius on EXACT match
        PipelineStage.FAILED
    ],
    PipelineStage.TEST_GENERATION: [PipelineStage.REVIEW_PENDING, PipelineStage.FAILED],
    PipelineStage.REVIEW_PENDING: [
        PipelineStage.REVIEW_APPROVED,
        PipelineStage.REVIEW_REJECTED,
        PipelineStage.FAILED
    ],
    PipelineStage.REVIEW_APPROVED: [PipelineStage.TESTRAIL_WRITE, PipelineStage.FAILED],
    PipelineStage.REVIEW_REJECTED: [PipelineStage.COMPLETED],
    PipelineStage.TESTRAIL_WRITE: [PipelineStage.BLAST_RADIUS, PipelineStage.FAILED],
    PipelineStage.BLAST_RADIUS: [PipelineStage.JIRA_CLOSE, PipelineStage.FAILED],
    PipelineStage.JIRA_CLOSE: [PipelineStage.COMPLETED],
    PipelineStage.COMPLETED: [],
    PipelineStage.FAILED: [],
}


def validate_transition(current: PipelineStage, target: PipelineStage) -> bool:
    """Check if a stage transition is valid."""
    allowed = STAGE_TRANSITIONS.get(current, [])
    return target in allowed


def get_next_stages(current: PipelineStage) -> list:
    """Get valid next stages from current."""
    return STAGE_TRANSITIONS.get(current, [])
