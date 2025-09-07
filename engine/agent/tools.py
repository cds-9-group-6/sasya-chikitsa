from __future__ import annotations
from typing import Optional, List, Callable

from langchain_core.tools import tool

from engine.agent.emitter import EmitterManager
from engine.ml.cnn_with_attention_classifier import CNNWithAttentionClassifier


class ClassificationTools:
    def __init__(
        self,
        model: CNNWithAttentionClassifier,
        emitter_mgr: EmitterManager,
        summarizer: Callable[[str], str],
        get_image_b64: Callable[[str], Optional[str]] | None = None,
        persist_result: Callable[[str, str, Optional[str]], None] | None = None,
    ) -> None:
        self.model = model
        self.emitter_mgr = emitter_mgr
        self.summarizer = summarizer
        self.get_image_b64 = get_image_b64  # provided by server at build time
        self.persist_result = persist_result  # provided by server at build time

    @tool("classify_leaf", return_direct=True)
    def classify_leaf(self, image_handle: str, text: Optional[str] = None, session_id: str = "default") -> str:
        """Classify a plant leaf image. Provide image_handle received from the system context, and optional text. Results are stored in session history."""
        if self.get_image_b64 is None:
            return "Image retrieval not configured."
        image_b64 = self.get_image_b64(image_handle)
        if not image_b64:
            return "No image found for provided handle."

        emitter = self.emitter_mgr.get_emitter()
        outputs: List[str] = []
        for chunk in self.model.predict_leaf_classification(image_b64, text or ""):
            chunk_str = str(chunk).rstrip("\n")
            outputs.append(chunk_str)
            if emitter:
                try:
                    emitter(chunk_str)
                except Exception:
                    pass

        # LLM-based summary and emit as final chunk
        summary = self.summarizer("\n".join(outputs))
        if emitter:
            try:
                emitter(summary)
            except Exception:
                pass

        # Persist results to session history
        current_session_id = self.emitter_mgr.current_session()
        if self.persist_result is not None:
            self.persist_result(current_session_id, "\n".join(outputs) + "\n\n" + summary, text)

        return "\n".join(outputs + ["", summary])


