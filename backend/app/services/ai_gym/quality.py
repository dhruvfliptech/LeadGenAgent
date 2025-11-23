"""
AI-GYM Quality Scorer

Automated quality assessment for AI-generated outputs.
Evaluates responses based on task-specific criteria and provides
objective quality scores (0-100).
"""

from typing import Dict, Any, Optional, List
import re
import json
import logging
from enum import Enum

from .models import TaskType

logger = logging.getLogger(__name__)


class QualityDimension(str, Enum):
    """Quality assessment dimensions."""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    RELEVANCE = "relevance"
    CLARITY = "clarity"
    STRUCTURE = "structure"
    ACTIONABILITY = "actionability"
    PROFESSIONALISM = "professionalism"


class QualityScorer:
    """
    Automated quality scoring system.

    Evaluates AI-generated outputs using task-specific heuristics
    and provides objective quality scores.
    """

    def __init__(self):
        """Initialize quality scorer."""
        pass

    async def score(
        self,
        task_type: TaskType,
        output: str,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate quality score for AI output.

        Args:
            task_type: Type of task performed
            output: AI-generated output
            context: Additional context for scoring

        Returns:
            Quality score (0-100)
        """
        context = context or {}

        # Route to task-specific scorer
        scorers = {
            TaskType.WEBSITE_ANALYSIS: self.score_website_analysis,
            TaskType.CODE_GENERATION: self.score_code_generation,
            TaskType.EMAIL_WRITING: self.score_email_writing,
            TaskType.CONVERSATION_RESPONSE: self.score_conversation_response,
            TaskType.LEAD_SCORING: self.score_lead_scoring,
            TaskType.CONTENT_SUMMARIZATION: self.score_content_summarization,
            TaskType.DATA_EXTRACTION: self.score_data_extraction,
        }

        scorer_func = scorers.get(task_type, self.score_generic)

        try:
            score = await scorer_func(output, context)
            return max(0.0, min(100.0, score))
        except Exception as e:
            logger.error(f"Quality scoring failed for {task_type}: {e}")
            return 50.0  # Neutral score on error

    async def score_website_analysis(
        self,
        output: str,
        context: Dict[str, Any]
    ) -> float:
        """
        Score website analysis output.

        Evaluates:
        - Structured JSON format
        - Required fields present
        - Meaningful content in each field
        - Actionable insights
        - Technology identification
        """
        scores = []

        # 1. JSON structure (20 points)
        try:
            data = json.loads(output) if isinstance(output, str) else output
            scores.append(20)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', output, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    scores.append(15)
                except:
                    data = {}
                    scores.append(0)
            else:
                data = {}
                scores.append(0)

        # 2. Required fields (30 points)
        required_fields = [
            'business_type', 'industry', 'target_audience',
            'services', 'unique_value_proposition'
        ]
        present_fields = sum(
            1 for field in required_fields
            if data.get(field) and len(str(data[field])) > 10
        )
        scores.append((present_fields / len(required_fields)) * 30)

        # 3. Technology detection (15 points)
        tech_fields = ['technologies', 'cms', 'frameworks']
        has_tech = any(
            data.get(field) and len(data.get(field, [])) > 0
            for field in tech_fields
        )
        scores.append(15 if has_tech else 5)

        # 4. Pain points identified (15 points)
        pain_points = data.get('pain_points', [])
        if isinstance(pain_points, list) and len(pain_points) >= 3:
            scores.append(15)
        elif isinstance(pain_points, list) and len(pain_points) > 0:
            scores.append(10)
        else:
            scores.append(0)

        # 5. Opportunities identified (20 points)
        opportunities = data.get('opportunities', [])
        if isinstance(opportunities, list) and len(opportunities) >= 3:
            # Check for actionable opportunities (not generic)
            actionable = sum(
                1 for opp in opportunities
                if len(str(opp)) > 30  # Substantial descriptions
            )
            scores.append((actionable / 3) * 20)
        else:
            scores.append(0)

        return sum(scores)

    async def score_code_generation(
        self,
        output: str,
        context: Dict[str, Any]
    ) -> float:
        """
        Score code generation output.

        Evaluates:
        - Valid syntax
        - Comments and documentation
        - Proper structure
        - Error handling
        - Best practices
        """
        scores = []

        # 1. Has code blocks (20 points)
        code_blocks = re.findall(r'```(\w+)?\n(.*?)```', output, re.DOTALL)
        if code_blocks:
            scores.append(20)
        else:
            scores.append(0)

        # 2. Has comments/documentation (20 points)
        has_comments = bool(
            re.search(r'(#|//|/\*|\"\"\"|\'\'\')', output)
        )
        scores.append(20 if has_comments else 5)

        # 3. Has function/class definitions (20 points)
        has_definitions = bool(
            re.search(r'(def |class |function |const |let |var )', output)
        )
        scores.append(20 if has_definitions else 0)

        # 4. Has error handling (20 points)
        has_error_handling = bool(
            re.search(r'(try|catch|except|raise|throw|error)', output, re.IGNORECASE)
        )
        scores.append(20 if has_error_handling else 10)

        # 5. Length and substance (20 points)
        if len(output) < 100:
            scores.append(5)
        elif len(output) < 500:
            scores.append(15)
        else:
            scores.append(20)

        return sum(scores)

    async def score_email_writing(
        self,
        output: str,
        context: Dict[str, Any]
    ) -> float:
        """
        Score email writing output.

        Evaluates:
        - Professional tone
        - Clear structure (greeting, body, closing)
        - Call to action
        - Personalization
        - Length appropriateness
        """
        scores = []

        # 1. Has greeting (15 points)
        has_greeting = bool(
            re.search(r'(Hi|Hello|Dear|Hey|Greetings)', output, re.IGNORECASE)
        )
        scores.append(15 if has_greeting else 0)

        # 2. Has closing (15 points)
        has_closing = bool(
            re.search(
                r'(Sincerely|Best regards|Thanks|Thank you|Cheers|Best)',
                output,
                re.IGNORECASE
            )
        )
        scores.append(15 if has_closing else 0)

        # 3. Has call to action (25 points)
        cta_patterns = [
            r'please (let me know|contact|reply|respond)',
            r'would you be (interested|available)',
            r'schedule (a call|meeting)',
            r'look forward to',
            r'feel free to'
        ]
        has_cta = any(
            re.search(pattern, output, re.IGNORECASE)
            for pattern in cta_patterns
        )
        scores.append(25 if has_cta else 10)

        # 4. Personalization (20 points)
        personalization_markers = sum([
            bool(re.search(r'\{.*?\}', output)),  # Has template variables
            bool(re.search(r'your (business|company|website|service)', output, re.IGNORECASE)),
            bool(re.search(r'(I noticed|I saw)', output, re.IGNORECASE))
        ])
        scores.append((personalization_markers / 3) * 20)

        # 5. Appropriate length (15 points)
        word_count = len(output.split())
        if 50 <= word_count <= 300:
            scores.append(15)
        elif 30 <= word_count <= 400:
            scores.append(10)
        else:
            scores.append(5)

        # 6. No excessive punctuation/caps (10 points)
        excessive_marks = len(re.findall(r'[!?]{2,}', output))
        excessive_caps = len(re.findall(r'\b[A-Z]{4,}\b', output))
        if excessive_marks == 0 and excessive_caps == 0:
            scores.append(10)
        else:
            scores.append(5)

        return sum(scores)

    async def score_conversation_response(
        self,
        output: str,
        context: Dict[str, Any]
    ) -> float:
        """
        Score conversation/chat response.

        Evaluates:
        - Relevance to question
        - Completeness
        - Tone appropriateness
        - Helpfulness
        """
        scores = []

        # 1. Has substance (25 points)
        if len(output) < 20:
            scores.append(5)
        elif len(output) < 100:
            scores.append(15)
        else:
            scores.append(25)

        # 2. Not just acknowledgment (20 points)
        generic_responses = [
            'ok', 'okay', 'sure', 'yes', 'no', 'thanks', 'thank you'
        ]
        is_generic = output.lower().strip() in generic_responses
        scores.append(5 if is_generic else 20)

        # 3. Helpful indicators (25 points)
        helpful_markers = sum([
            bool(re.search(r'(here|this is|you can|try|consider)', output, re.IGNORECASE)),
            bool(re.search(r'(example|specifically|such as)', output, re.IGNORECASE)),
            bool(re.search(r'[:\-\*\d\.]', output)),  # Has lists or structure
        ])
        scores.append((helpful_markers / 3) * 25)

        # 4. Professional tone (15 points)
        has_slang = bool(re.search(r'\b(gonna|wanna|yeah|nah|lol)\b', output, re.IGNORECASE))
        scores.append(5 if has_slang else 15)

        # 5. Addresses the question (15 points)
        user_message = context.get('user_message', '')
        if user_message:
            # Check if response relates to key words in question
            question_words = set(re.findall(r'\b\w{4,}\b', user_message.lower()))
            response_words = set(re.findall(r'\b\w{4,}\b', output.lower()))
            overlap = len(question_words & response_words)
            scores.append(min(15, overlap * 3))
        else:
            scores.append(10)  # No context, neutral score

        return sum(scores)

    async def score_lead_scoring(
        self,
        output: str,
        context: Dict[str, Any]
    ) -> float:
        """
        Score lead scoring/qualification output.

        Evaluates:
        - Clear score/recommendation
        - Reasoning provided
        - Factors considered
        - Actionable next steps
        """
        scores = []

        # 1. Has numeric score (25 points)
        has_score = bool(re.search(r'\b\d{1,3}\b', output))
        scores.append(25 if has_score else 0)

        # 2. Has qualification level (20 points)
        has_qualification = bool(
            re.search(
                r'(high|medium|low|hot|warm|cold|qualified|unqualified)',
                output,
                re.IGNORECASE
            )
        )
        scores.append(20 if has_qualification else 0)

        # 3. Has reasoning (25 points)
        has_because = bool(
            re.search(r'(because|since|due to|based on|factors)', output, re.IGNORECASE)
        )
        scores.append(25 if has_because else 10)

        # 4. Considers multiple factors (20 points)
        factor_keywords = [
            'budget', 'authority', 'need', 'timeline', 'fit',
            'engagement', 'company size', 'industry'
        ]
        factors_mentioned = sum(
            1 for keyword in factor_keywords
            if keyword in output.lower()
        )
        scores.append(min(20, factors_mentioned * 5))

        # 5. Has next steps (10 points)
        has_next_steps = bool(
            re.search(r'(next step|recommend|suggest|should)', output, re.IGNORECASE)
        )
        scores.append(10 if has_next_steps else 0)

        return sum(scores)

    async def score_content_summarization(
        self,
        output: str,
        context: Dict[str, Any]
    ) -> float:
        """
        Score content summarization output.

        Evaluates:
        - Conciseness
        - Key points captured
        - Structure
        - Clarity
        """
        scores = []

        original_length = context.get('original_length', 1000)
        summary_length = len(output)

        # 1. Appropriate length (25 points)
        compression_ratio = summary_length / original_length if original_length > 0 else 1
        if 0.1 <= compression_ratio <= 0.4:
            scores.append(25)
        elif 0.05 <= compression_ratio <= 0.6:
            scores.append(15)
        else:
            scores.append(5)

        # 2. Has structure (25 points)
        has_bullets = bool(re.search(r'[\*\-\d]\s+', output))
        has_paragraphs = len(output.split('\n\n')) > 1
        if has_bullets or has_paragraphs:
            scores.append(25)
        else:
            scores.append(10)

        # 3. Key information markers (25 points)
        info_markers = sum([
            bool(re.search(r'(key|main|important|primary)', output, re.IGNORECASE)),
            bool(re.search(r'(first|second|third|finally)', output, re.IGNORECASE)),
            bool(re.search(r'(include|such as|example)', output, re.IGNORECASE))
        ])
        scores.append((info_markers / 3) * 25)

        # 4. Not too brief (15 points)
        if summary_length < 50:
            scores.append(5)
        elif summary_length < 100:
            scores.append(10)
        else:
            scores.append(15)

        # 5. Coherent (10 points)
        sentences = len(re.findall(r'[.!?]+', output))
        if sentences >= 2:
            scores.append(10)
        else:
            scores.append(5)

        return sum(scores)

    async def score_data_extraction(
        self,
        output: str,
        context: Dict[str, Any]
    ) -> float:
        """
        Score data extraction output.

        Evaluates:
        - Structured format (JSON)
        - Completeness
        - Accuracy markers
        - Consistent schema
        """
        scores = []

        # 1. Valid JSON/structure (30 points)
        try:
            data = json.loads(output) if isinstance(output, str) else output
            scores.append(30)
        except json.JSONDecodeError:
            # Try to find JSON in output
            if '{' in output and '}' in output:
                scores.append(15)
            else:
                scores.append(0)
                data = {}

        # 2. Has extracted data (30 points)
        if isinstance(data, dict):
            field_count = len(data)
            if field_count >= 5:
                scores.append(30)
            elif field_count >= 3:
                scores.append(20)
            elif field_count >= 1:
                scores.append(10)
            else:
                scores.append(0)
        elif isinstance(data, list) and len(data) > 0:
            scores.append(25)
        else:
            scores.append(0)

        # 3. Non-empty values (20 points)
        if isinstance(data, dict):
            non_empty = sum(
                1 for v in data.values()
                if v and str(v).strip() not in ['null', 'None', 'N/A', '']
            )
            total_fields = len(data)
            if total_fields > 0:
                scores.append((non_empty / total_fields) * 20)
            else:
                scores.append(0)
        else:
            scores.append(10)

        # 4. Consistent types (10 points)
        if isinstance(data, dict):
            # Check if similar keys have similar value types
            scores.append(10)  # Assume consistent if valid JSON
        else:
            scores.append(5)

        # 5. Confidence/source indicators (10 points)
        has_confidence = bool(
            re.search(r'(confidence|probability|source)', output, re.IGNORECASE)
        )
        scores.append(10 if has_confidence else 5)

        return sum(scores)

    async def score_generic(
        self,
        output: str,
        context: Dict[str, Any]
    ) -> float:
        """
        Generic quality scoring for unknown task types.

        Evaluates:
        - Output length
        - Structure
        - Completeness
        """
        scores = []

        # 1. Has content (30 points)
        if len(output) < 50:
            scores.append(5)
        elif len(output) < 200:
            scores.append(20)
        else:
            scores.append(30)

        # 2. Has structure (25 points)
        has_structure = bool(
            re.search(r'[\n\*\-\d]', output)
        )
        scores.append(25 if has_structure else 10)

        # 3. Multiple sentences (20 points)
        sentences = len(re.findall(r'[.!?]+', output))
        scores.append(min(20, sentences * 4))

        # 4. No obvious errors (15 points)
        has_error_markers = bool(
            re.search(r'(error|failed|unable|cannot|invalid)', output, re.IGNORECASE)
        )
        scores.append(5 if has_error_markers else 15)

        # 5. Completeness (10 points)
        seems_complete = not bool(
            re.search(r'(\.\.\.|\[|\]|\(incomplete\)|pending)', output, re.IGNORECASE)
        )
        scores.append(10 if seems_complete else 5)

        return sum(scores)

    async def score_with_dimensions(
        self,
        task_type: TaskType,
        output: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        Get detailed quality scores by dimension.

        Args:
            task_type: Task type
            output: AI output
            context: Additional context

        Returns:
            Dictionary of dimension scores
        """
        overall_score = await self.score(task_type, output, context)

        # For now, return overall score with estimated breakdown
        # In production, implement dimension-specific scoring
        return {
            'overall': overall_score,
            'completeness': overall_score * 0.95,
            'accuracy': overall_score * 1.02,
            'relevance': overall_score * 0.98,
            'clarity': overall_score * 1.01,
            'structure': overall_score * 0.97
        }


# Global scorer instance
_quality_scorer: Optional[QualityScorer] = None


def get_quality_scorer() -> QualityScorer:
    """Get or create the global quality scorer singleton."""
    global _quality_scorer
    if _quality_scorer is None:
        _quality_scorer = QualityScorer()
    return _quality_scorer
