import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import pandas as pd
import re
from tqdm import tqdm
from .NoiseConverter import NoiseConverter
from typing import Tuple, Optional

class NCGemma2(NoiseConverter):
    
    def __init__(self, model_id: str = "rtzr/ko-gemma-2-9b-it"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        
    def _convert_row(self, row: pd.Series) -> Tuple[str, int, int, Optional[str]]:
        """행 하나에 대해서 노이즈를 복원하는 함수

        Args:
            row (pd.Series): 노이즈가 있는 행

        Returns:
            Tuple[str, int, int, Optional[str]]: 
            - 복원된 텍스트
            - 텍스트의 label (0~6)
            - 노이즈가 있는지 여부 (1: 노이즈 있음, 0: 노이즈 없음)
            - reason : 텍스트 복원 방법에 대한 설명 (Optional)
        """
        
        text = row['text']
        label = row['target']
        
        messages = [
        {
        "role": "system",
        "content": (
        "Guidelines:\n"
        "1. Context Understanding: Prioritize comprehension of each sentence’s main theme and intent to ensure natural, accurate Korean expression.\n\n"
        "2. Character Handling:\n"
        " - CRITICAL: Never convert Chinese characters (한자) to Hangul; Chinese characters are essential and not noise.\n"
        " - Remove special characters if they do not affect meaning or flow.\n"
        " - Convert numbers to Korean words only if necessary for context.\n\n"
        "3. Text Preservation and Restoration:\n"
        " - Keep the original text if grammatically correct and contextually appropriate.\n"
        " - For noise in the text, translate it into appropriate Korean syllables.\n"
        " - Restore proper nouns accurately to preserve intended meaning.\n\n"
        "4. Grammar and Structure:\n"
        " - Adjust particles, endings, or conjunctions only if clearly incorrect.\n"
        " - Preserve original sentence structure if it is sound, and apply minimal changes only when essential for clarity.\n\n"
        "5. Spacing and Formatting:\n"
        " - Correct only obvious spacing errors.\n"
        " - Make spacing adjustments only if they improve readability without altering the intended style.\n\n"
        "6. Noise and Content Evaluation:\n"
        " - Label noise as 1 if characters impair comprehension or clarity.\n"
        " - Do not mark Chinese characters as noise, even if translated into Hangul.\n"
        " - Maintain original stylistic elements unless they obstruct understanding.\n\n"
        "7. Contextual Consistency:\n"
        " - Use surrounding context to validate any modifications.\n"
        " - Differentiate between formal and informal writing styles, respecting genre and writing conventions.\n\n"
        "8. Korean Language Standards:\n"
        " - Ensure modifications adhere to Korean grammar rules.\n"
        " - Preserve intentional stylistic deviations from standard forms if they enhance meaning or style.\n\n"
        "Precautions:\n"
        " - Top Priority: Never convert or mark Chinese characters (한자) as noise.\n"
        " - When uncertain, keep the original text if comprehensible.\n"
        " - Handle loanwords carefully and preserve intentional stylistic elements.\n\n"
        "Objective: Carefully evaluate each text, making essential modifications only to improve comprehension or correct evident errors. All Chinese characters must remain in their original form, and intentional stylistic choices should be preserved. Aim to produce clear, natural Korean text that maintains the author’s voice and original intent."
        )},
        {"role": "user", "content": "text: '갯벌도 얼려버린^한파'\nlabel: 0"},
        {"role": "assistant", "content": "text: '갯벌도 얼려버린 혹한'\nlabel: 0\nnoise: 1"},
        {"role": "user", "content": "text: '與 대표 선출, 친박·비박 구도 격화'\nlabel: 2"},
        {"role": "assistant", "content": "text: '與 대표 선출, 친박·비박 구도 격화'\nlabel: 2\nnoise: 0"},
        {"role": "user", "content": "text: 'cI그1[사령탑이 탐내C 선t는…이재성·이근호'\nlabel: 1"},
        {"role": "assistant", "content": "text: '이강인 사령탑이 탐내는…이재성·이근호'\nlabel: 1\nnoise: 1"},
        {"role": "user", "content": "text: '새누리 원내대표 CL 화|는,여소야대·계파'\nlabel: 2"},
        {"role": "assistant", "content": "text: '새누리 원내대표 경선, 여소야대·계파'\nlabel: 2\nnoise: 1"},
        {"role": "user", "content": "text: '감사원 수과학j구소M연구보다h워크>·강연'\nlabel: 3"},
        {"role": "assistant", "content": "text: '감사원 수학과학 연구소 연구보다 워크숍·강연'\nlabel: 3\nnoise: 1"},
        {"role": "user", "content": "text: '이통Y사f갤럭시탭Sr 오늘w터L사전예약 시작'\nlabel: 4"},
        {"role": "assistant", "content": "text: '이통3사 갤럭시탭S8 오늘부터 사전예약 시작'\nlabel: 4\nnoise: 1"},
        {"role": "user", "content": "text: 'T시판 H성선물 하반기 p율·유가U망 세미나'\nlabel: 5"},
        {"role": "assistant", "content": "text: 'T시판 H성선물 하반기 금리·유가 전망 세미나'\nlabel: 5\nnoise: 1"},
        {"role": "user", "content": "text: '與 김재수 해임건의안 제출에 옹졸한 정치보복성 공세종합'\nlabel: 2"},
        {"role": "assistant", "content": "text: '與 김재수 해임건의안 제출에 옹졸한 정치보복성 공세종합'\nlabel: 2\nnoise: 0"},
        {"role": "user", "content": "text: '중국의 해외투자 안전도I평가서 Z국 O위→=_위t추락'\nlabel: 6"},
        {"role": "assistant", "content": "text: '중국의 해외투자 안전도 평가서 1위 → 3위 추락'\nlabel: 6\nnoise: 1"},
        {"role": "user", "content": "text: '박상R·w}욱 c 시B 6권 현대문학 *s시 즈 첫^출간'\nlabel: 5"},
        {"role": "assistant", "content": "text: '박상규·욱 시집 6권 현대문학 시리즈 첫 출간'\nlabel: 5\nnoise: 1"},
        {"role": "user", "content": "text: '미스터 _샤인 S프로 부^…인물들 납y해'\nlabel: 0"},
        {"role": "assistant", "content": "text: '미스터 션샤인 OST 프로듀서 부부…인물들 납득해'\nlabel: 0\nnoise: 1"},
        {"role": "user", "content": "text: '월드컵 r안하|는 말/반%한G손흥' 울지c않으려고H..'\nlabel: 1"},
        {"role": "assistant", "content": "text: '월드컵 안하는 말 반박한 손흥민 울지 않으려고...''\nlabel: 1\nnoise: 1"},
        {"role": "user", "content": "text: '北0대! 김정*2향한 '성경쟁 무대된l릴레이r토론''\nlabel: 2"},
        {"role": "assistant", "content": "text: '北 핵! 김정은 향한 '성경쟁 무대된 릴레이 토론''\nlabel: 2\nnoise: 1"},
        {"role": "user", "content": "text: '안경은%X: 보O기i 안되고…경찰관 공채u신체3준 논란'\nlabel: 3"},
        {"role": "assistant", "content": "text: '안경은 시력 보정이 안되고…경찰관 공채 신체기준 논란'\nlabel: 3\nnoise: 1"},
        {"role": "user", "content": "text: '이녹스 1분기 영업이익 17억원…76% 감소'\nlabel: 3"},
        {"role": "assistant", "content": "text: '이녹스 1분기 영업이익 17억원…76% 감소'\nlabel: 3\nnoise: 0"},
        {"role": "user", "content": "text: '위클리 스마트d스트레8E~N엔 휴,·면역강화엔 명상 과C적 l증'\nlabel: 4"},
        {"role": "assistant", "content": "text: '위클리 스마트스트레칭, 면역강화엔 명상과 적절한 운동'\nlabel: 4\nnoise: 1"},
        {"role": "user", "content": "text: '국토h 공동주택 관리 n우수0지에M서울 텐r힐 1단지'\nlabel: 5"},
        {"role": "assistant", "content": "text: '국토부 공동주택 관리 우수단지에 서울 텐즈힐 1단지'\nlabel: 5\nnoise: 1"},
        {"role": "user", "content": "text: '이탈리아^독일~wGn난민구조선~억9…S6규정n등 위반'\nlabel: 6"},
        {"role": "assistant", "content": "text: '이탈리아·독일 NGO 난민구조선 억류…EU 규정 등 위반'\nlabel: 6\nnoise: 1"},
        {"role": "user", "content": f"text: '{text}'\nlabel: {label}"}]
        
        input_ids = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to(self.model.device)
        
        terminators = [
            self.tokenizer.eos_token_id,
            self.tokenizer.convert_tokens_to_ids("<end_of_turn>")
        ]
        
        outputs = self.model.generate(
            input_ids,
            max_new_tokens=2048,
            eos_token_id=terminators,
            do_sample=True,
            temperature=0.6,
            top_p=0.9,
        )
        
        output = self.tokenizer.decode(outputs[0][input_ids.shape[-1]:], skip_special_tokens=True)
        
        cleaned_text = re.search(r"text:\s'([^']*)'", output).group(1) if re.search(r"text:\s'([^']*)'", output) else ""
        label = int(re.search(r"label:\s(\d+)", output).group(1)) if re.search(r"label:\s(\d+)", output) else ""
        noise = re.search(r"noise:\s([10])", output).group(1) if re.search(r"noise:\s([10])", output) else ""
        reason_match = re.search(r"reason:\s(.+)", output)
        reason = reason_match.group(1).strip() if reason_match else ""

        return cleaned_text, label, noise, reason
    
    def convert(self, df: pd.DataFrame) -> pd.DataFrame:
        """노이즈가 존재하는 dataframe을 받아 입력한 프롬프트로 노이즈를 복원하여 반환하는 function

        Args:
            df (pd.DataFrame): 모든 행에 noise가 존재하는 dataframe

        Returns:
            pd.DataFrame: noise가 복원된 dataframe
        """
        results = []
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing rows"):
            cleaned_text, label, noise, reason = self._convert_row(row)
            results.append({
                'ID': row['ID'],
                'original': row['text'],
                'text': cleaned_text,
                'target': label,
                'noise': noise,
                # 'reason': reason
            })
        
        results_df = pd.DataFrame(results)
        return results_df