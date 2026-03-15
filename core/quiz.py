import json
import os
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class QuizQuestion:
    id: str
    question: str
    correct_answer: str
    alternatives: List[str]
    relationship_type: str
    source_node_text: str
    related_node_text: str
    explanation: str
    times_shown: int = 0
    times_correct: int = 0
    user_corrected_answer: Optional[str] = None
    
    @property
    def effective_correct_answer(self) -> str:
        return self.user_corrected_answer if self.user_corrected_answer else self.correct_answer
    
    @property
    def is_wrong_often(self) -> bool:
        if self.times_shown == 0:
            return False
        return self.times_correct / self.times_shown < 0.7


@dataclass  
class QuizState:
    consecutive_correct: int = 0
    questions: List[QuizQuestion] = field(default_factory=list)
    current_question_index: int = -1
    current_file_path: Optional[str] = None
    
    def get_question_pool(self) -> List[QuizQuestion]:
        pool = []
        wrong_often = [q for q in self.questions if q.is_wrong_often]
        pool.extend(wrong_often * 3)
        pool.extend(self.questions)
        random.shuffle(pool)
        return pool


class QuizManager:
    RELATIONSHIP_PATTERNS = [
        ("conceito", ["é o conceito de", "conceito de", "definido como", "significa"]),
        ("tipo", ["é um tipo de", "são tipos de", "tipo de", "categorias de"]),
        ("exemplo", ["é exemplo de", "são exemplos de", "exemplos de", "como"]),
        ("diferenca", ["diferença entre", "diferente de", "distingue-se por", "ao contrário de"]),
        ("parte", ["é parte de", "faz parte de", "componente de", "subdivisão de"]),
        ("causa", ["causa de", "provoca", "resulta em", "leva a"]),
        ("efeito", ["efeito de", "resultado de", "consequência de"]),
        ("relacao", ["relacionado a", "conectado a", "associado a", "vinculado a"]),
    ]
    
    def __init__(self):
        self.state = QuizState()
        self._load_history()
    
    def _get_history_path(self) -> str:
        app_data = os.path.expanduser("~")
        return os.path.join(app_data, ".amarelo_mind", "quiz_history.json")
    
    def _load_history(self):
        path = self._get_history_path()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.state.consecutive_correct = data.get("consecutive_correct", 0)
                    for q_data in data.get("questions", []):
                        q = QuizQuestion(
                            id=q_data["id"],
                            question=q_data["question"],
                            correct_answer=q_data["correct_answer"],
                            alternatives=q_data["alternatives"],
                            relationship_type=q_data["relationship_type"],
                            source_node_text=q_data["source_node_text"],
                            related_node_text=q_data["related_node_text"],
                            explanation=q_data["explanation"],
                            times_shown=q_data.get("times_shown", 0),
                            times_correct=q_data.get("times_correct", 0),
                            user_corrected_answer=q_data.get("user_corrected_answer")
                        )
                        self.state.questions.append(q)
            except Exception as e:
                print(f"Erro ao carregar histórico de quiz: {e}")
    
    def _save_history(self):
        path = self._get_history_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            data = {
                "consecutive_correct": self.state.consecutive_correct,
                "questions": [
                    {
                        "id": q.id,
                        "question": q.question,
                        "correct_answer": q.correct_answer,
                        "alternatives": q.alternatives,
                        "relationship_type": q.relationship_type,
                        "source_node_text": q.source_node_text,
                        "related_node_text": q.related_node_text,
                        "explanation": q.explanation,
                        "times_shown": q.times_shown,
                        "times_correct": q.times_correct,
                        "user_corrected_answer": q.user_corrected_answer
                    }
                    for q in self.state.questions
                ]
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar histórico de quiz: {e}")
    
    def analyze_scene(self, scene, file_path: Optional[str] = None):
        from items.shapes import StyledNode
        from core.connection import SmartConnection
        
        self.state.current_file_path = file_path
        
        nodes = []
        for item in scene.items():
            if isinstance(item, StyledNode):
                text = item.get_text().strip()
                if text:
                    nodes.append({"node": item, "text": text})
        
        connections = []
        for item in scene.items():
            if isinstance(item, SmartConnection):
                source_text = item.source.get_text().strip() if hasattr(item.source, 'get_text') else ""
                target_text = item.target.get_text().strip() if hasattr(item.target, 'get_text') else ""
                if source_text and target_text:
                    connections.append({
                        "source": source_text,
                        "target": target_text,
                        "source_node": item.source,
                        "target_node": item.target
                    })
        
        self._generate_questions(nodes, connections)
        return len(self.state.questions) > 0
    
    def _generate_questions(self, nodes: List[Dict], connections: List[Dict]):
        existing_questions = {q.source_node_text + "|" + q.related_node_text: q 
                            for q in self.state.questions}
        
        new_questions = []
        
        for conn in connections:
            source = conn["source"]
            target = conn["target"]
            rel_type = self._detect_relationship(source, target)
            
            key = source + "|" + target
            if key in existing_questions:
                continue
            
            question = self._create_question(source, target, rel_type, nodes)
            if question:
                new_questions.append(question)
                existing_questions[key] = question
        
        self.state.questions.extend(new_questions)
        self._save_history()
    
    def _detect_relationship(self, source: str, target: str) -> str:
        source_lower = source.lower()
        target_lower = target.lower()
        
        for rel_type, patterns in self.RELATIONSHIP_PATTERNS:
            for pattern in patterns:
                if pattern in source_lower or pattern in target_lower:
                    return rel_type
        return "relacao"
    
    def _create_question(self, source: str, target: str, rel_type: str, 
                        all_nodes: List[Dict]) -> Optional[QuizQuestion]:
        all_texts = [n["text"] for n in all_nodes if n["text"] != source and n["text"] != target]
        
        templates = self._get_question_templates(rel_type)
        if not templates:
            return None
        
        template = random.choice(templates)
        
        question_text = template["question"].format(subject=target)
        
        if template.get("inverted"):
            question_text = template["question"].format(subject=source)
        
        correct = target if not template.get("inverted") else source
        
        alternatives = self._generate_alternatives(correct, all_texts, 4)
        
        explanation = template["explanation"].format(
            correct=correct,
            subject=source if template.get("inverted") else target,
            other=source if not template.get("inverted") else target
        )
        
        q_id = f"{hash(source + '|' + target) % 100000}"
        
        return QuizQuestion(
            id=q_id,
            question=question_text,
            correct_answer=correct,
            alternatives=alternatives,
            relationship_type=rel_type,
            source_node_text=source,
            related_node_text=target,
            explanation=explanation
        )
    
    def _get_question_templates(self, rel_type: str) -> List[Dict]:
        templates_map = {
            "conceito": [
                {
                    "question": "O que é {subject}?",
                    "explanation": "{subject} é o conceito de {other}. As demais opções não definem {subject} corretamente."
                },
                {
                    "question": "Qual é a definição de {subject}?",
                    "explanation": "{subject} representa {other}. As outras alternativas não correspondem à definição de {subject}."
                }
            ],
            "tipo": [
                {
                    "question": "Qual é um tipo de {subject}?",
                    "explanation": "{subject} é um tipo de {other}. As demais opções são categorias diferentes."
                },
                {
                    "question": "{subject} é um exemplo de que categoria?",
                    "inverted": True,
                    "explanation": "{other} é a categoria geral, e {subject} é um tipo específico dela."
                }
            ],
            "exemplo": [
                {
                    "question": "Qual é um exemplo de {subject}?",
                    "explanation": "{subject} é um exemplo de {other}. As demais opções não são exemplos de {other}."
                },
                {
                    "question": "{subject} exemplifica o quê?",
                    "inverted": True,
                    "explanation": "{other} é exemplificado por {subject}."
                }
            ],
            "diferenca": [
                {
                    "question": "Qual é a diferença de {subject}?",
                    "explanation": "{subject} difere de {other} porque {subject} tem características distintas."
                }
            ],
            "parte": [
                {
                    "question": "O que faz parte de {subject}?",
                    "explanation": "{subject} é parte de {other}. As demais opções não são componentes de {other}."
                }
            ],
            "causa": [
                {
                    "question": "O que causa {subject}?",
                    "explanation": "{other} causa {subject}. As outras opções não estão relacionadas causalmente."
                }
            ],
            "efeito": [
                {
                    "question": "Qual é o efeito de {subject}?",
                    "explanation": "{other} é o efeito de {subject}. As demais opções não são consequências de {subject}."
                }
            ],
            "relacao": [
                {
                    "question": "O que está relacionado a {subject}?",
                    "explanation": "{subject} está relacionado a {other}. As demais opções não têm relação direta."
                },
                {
                    "question": "Como {subject} se conecta a outros conceitos?",
                    "explanation": "{subject} se conecta a {other} no mapa mental."
                }
            ]
        }
        return templates_map.get(rel_type, templates_map.get("relacao"))
    
    def _generate_alternatives(self, correct: str, all_texts: List[str], count: int) -> List[str]:
        alternatives = [correct]
        available = [t for t in all_texts if t != correct]
        random.shuffle(available)
        
        for text in available:
            if len(alternatives) >= count:
                break
            if text and len(text) > 1:
                alternatives.append(text)
        
        while len(alternatives) < count:
            alternatives.append(f"Opção {len(alternatives) + 1}")
        
        random.shuffle(alternatives)
        return alternatives[:count]
    
    def get_next_question(self) -> Optional[QuizQuestion]:
        pool = self.state.get_question_pool()
        
        if not pool:
            return None
        
        if self.state.current_question_index + 1 < len(pool):
            self.state.current_question_index += 1
        else:
            self.state.current_question_index = 0
            random.shuffle(pool)
        
        q = pool[self.state.current_question_index]
        q.times_shown += 1
        self._save_history()
        return q
    
    def answer_question(self, question_id: str, answer: str) -> Dict[str, Any]:
        for q in self.state.questions:
            if q.id == question_id:
                is_correct = (answer == q.effective_correct_answer)
                
                if is_correct:
                    q.times_correct += 1
                    self.state.consecutive_correct += 1
                else:
                    self.state.consecutive_correct = 0
                
                self._save_history()
                
                return {
                    "correct": is_correct,
                    "correct_answer": q.effective_correct_answer,
                    "explanation": q.explanation,
                    "consecutive": self.state.consecutive_correct
                }
        
        return {"correct": False, "error": "Questão não encontrada"}
    
    def correct_answer(self, question_id: str, new_correct_answer: str):
        for q in self.state.questions:
            if q.id == question_id:
                q.user_corrected_answer = new_correct_answer
                self._save_history()
                return True
        return False
    
    def get_consecutive_count(self) -> int:
        return self.state.consecutive_correct
    
    def has_questions(self) -> bool:
        return len(self.state.questions) > 0
