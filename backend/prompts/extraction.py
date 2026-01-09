"""
Entity Extraction Prompts
==========================

Prompt templates for Named Entity Recognition (NER) and Relationship Extraction.

Prompt Engineering Principles Applied:
--------------------------------------
1. **Clarity**: Explicit instructions on what to extract
2. **Structure**: Define exact JSON schema expected
3. **Examples**: Show what good output looks like
4. **Constraints**: Set boundaries (confidence scores, types)
5. **Context**: Explain why we need each field

Version History:
- v1.0: Initial prompt for tech entity extraction
"""

from string import Template

# System-level instruction (sets LLM behavior)
NER_SYSTEM_PROMPT = """You are an expert AI system specialized in Named Entity Recognition (NER) and Relationship Extraction.

Your task is to analyze text and extract:
1. **Entities** (nodes): Technologies, Concepts, People, Organizations
2. **Relationships** (edges): How entities are connected

Be precise and only extract meaningful, clearly stated connections. If unsure about a relationship, don't create it.

Quality guidelines:
- Confidence scores should reflect certainty (0.0 - 1.0)
- Use descriptive relation names (e.g., "used_for" not "relates_to")
- Normalize entity names (e.g., "PostgreSQL" not "postgres")
- Avoid duplicate or redundant relationships
"""


# User prompt template
EXTRACTION_TEMPLATE = Template("""Analyze the following text and extract entities and their relationships:

TEXT TO ANALYZE:
\"\"\"
$text
\"\"\"

INSTRUCTIONS:
1. Extract all relevant entities (nodes):
   - **id**: Lowercase, hyphenated identifier (e.g., "machine-learning")
   - **label**: Human-readable name (e.g., "Machine Learning")
   - **type**: One of: "Tech", "Concept", "Person", "Organization"
   - **confidence**: 0.0-1.0 score based on clarity and context
     * 0.9-1.0: Explicitly mentioned, clear context
     * 0.7-0.89: Clearly mentioned, some context
     * 0.5-0.69: Mentioned but ambiguous
     * Below 0.5: Don't extract

2. Extract relationships (edges) between entities:
   - **source**: ID of source entity
   - **target**: ID of target entity
   - **relation**: Verb phrase describing relationship
     * Examples: "used_for", "implements", "created_by", "part_of", "enables"

3. Output format:
   - Return ONLY valid JSON
   - No explanatory text before or after
   - Match the schema exactly

EXAMPLE OUTPUT:
{
  "nodes": [
    {"id": "python", "label": "Python", "type": "Tech", "confidence": 0.95},
    {"id": "data-science", "label": "Data Science", "type": "Concept", "confidence": 0.9}
  ],
  "edges": [
    {"source": "python", "target": "data-science", "relation": "used_for"}
  ]
}

Now extract entities and relationships from the text above. Return only JSON:
""")


def build_extraction_prompt(text: str) -> str:
    """
    Build complete extraction prompt from template.

    Learning Note:
    We use string.Template instead of f-strings because:
    1. Safer (prevents code injection if text comes from users)
    2. Can load templates from files later
    3. Clear separation of template and data

    Args:
        text: Input text to analyze

    Returns:
        Complete prompt ready for LLM

    Example:
        >>> prompt = build_extraction_prompt("Python is used for AI")
        >>> print(prompt[:50])
        'Analyze the following text and extract entities...'
    """
    return EXTRACTION_TEMPLATE.substitute(text=text)


# Advanced: Few-shot learning prompt (with examples)
FEW_SHOT_TEMPLATE = Template("""Analyze text and extract entities and relationships.

EXAMPLE 1:
Input: "React is a JavaScript library for building user interfaces"
Output:
{
  "nodes": [
    {"id": "react", "label": "React", "type": "Tech", "confidence": 0.95},
    {"id": "javascript", "label": "JavaScript", "type": "Tech", "confidence": 0.9},
    {"id": "user-interfaces", "label": "User Interfaces", "type": "Concept", "confidence": 0.85}
  ],
  "edges": [
    {"source": "react", "target": "javascript", "relation": "built_with"},
    {"source": "react", "target": "user-interfaces", "relation": "used_for"}
  ]
}

EXAMPLE 2:
Input: "Docker containerizes applications for easier deployment"
Output:
{
  "nodes": [
    {"id": "docker", "label": "Docker", "type": "Tech", "confidence": 0.95},
    {"id": "applications", "label": "Applications", "type": "Concept", "confidence": 0.8},
    {"id": "deployment", "label": "Deployment", "type": "Concept", "confidence": 0.85}
  ],
  "edges": [
    {"source": "docker", "target": "applications", "relation": "containerizes"},
    {"source": "docker", "target": "deployment", "relation": "enables"}
  ]
}

NOW YOUR TURN:
Input: "$text"
Output (JSON only):
""")


def build_few_shot_prompt(text: str) -> str:
    """
    Build few-shot prompt with examples.

    Learning Note - Few-Shot Learning:
    Providing examples helps the LLM understand:
    1. Expected output format
    2. Appropriate confidence scores
    3. Relationship naming conventions
    4. Level of detail required

    Use this when you need higher quality extraction.

    Args:
        text: Input text to analyze

    Returns:
        Prompt with examples
    """
    return FEW_SHOT_TEMPLATE.substitute(text=text)
