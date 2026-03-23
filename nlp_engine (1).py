import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoModelForSeq2SeqLM
import vector_store

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoModelForSeq2SeqLM
import vector_store

MODEL_ID = "Qwen/Qwen2.5-3B-Instruct"
# Downgraded the translator to free up 1.5GB of VRAM
TRANSLATOR_ID = "facebook/nllb-200-distilled-600M" 

model = None
tokenizer = None
translator_model = None
translator_tokenizer = None

def init_model():
    global model, tokenizer, translator_model, translator_tokenizer

    if model is None:
        print(f"Loading {MODEL_ID} in 4-bit mode...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        
        # CHANGED: 4-bit mode shrinks the model to ~2GB and is highly optimized
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            device_map="auto",
            load_in_4bit=True, 
        )

        print(f"Loading {TRANSLATOR_ID}...")
        translator_tokenizer = AutoTokenizer.from_pretrained(TRANSLATOR_ID)
        translator_model = AutoModelForSeq2SeqLM.from_pretrained(
            TRANSLATOR_ID,
            device_map="auto",
            torch_dtype=torch.float16
        )
        print("✅ Models loaded! VRAM should be breathing easy now.")

LANG_CODES = {
    "English": "eng_Latn",
    # --- International ---
    "French": "fra_Latn",
    "German": "deu_Latn",
    "Japanese": "jpn_Jpan",

    # --- Indian Languages (Major & Regional) ---
    "Assamese": "asm_Beng",
    "Bengali": "ben_Beng",
    "Bhojpuri": "bho_Deva",
    "Gujarati": "guj_Gujr",
    "Hindi": "hin_Deva",
    "Kannada": "kan_Knda",
    "Kashmiri (Arabic)": "kas_Arab",
    "Kashmiri (Devanagari)": "kas_Deva",
    "Maithili": "mai_Deva",
    "Malayalam": "mal_Mlym",
    "Marathi": "mar_Deva",
    "Meitei (Manipuri)": "mni_Beng",
    "Nepali": "npi_Deva",
    "Odia": "ory_Orya",
    "Punjabi": "pan_Guru",
    "Sanskrit": "san_Deva",
    "Santali": "sat_Beng",
    "Sindhi": "snd_Arab",
    "Tamil": "tam_Taml",
    "Telugu": "tel_Telu",
    "Urdu": "urd_Arab",
}

def translate_fast(text, source_lang, target_lang):
    if translator_model is None:
        init_model()

    if source_lang == target_lang:
        return text

    src_code = LANG_CODES.get(source_lang, "eng_Latn")
    tgt_code = LANG_CODES.get(target_lang, "eng_Latn")

    translator_tokenizer.src_lang = src_code
    inputs = translator_tokenizer(
        text,
        return_tensors="pt",
        max_length=512,
        truncation=True
    ).to(translator_model.device)

    tgt_token_id = translator_tokenizer.convert_tokens_to_ids(tgt_code)

    outputs = translator_model.generate(
        **inputs,
        forced_bos_token_id=tgt_token_id,
        max_length=512,
        num_beams=2
    )

    return translator_tokenizer.decode(outputs[0], skip_special_tokens=True)

def generate_english_response(prompt_text):
    if model is None:
        init_model()

    # 🚀 UPGRADE 3: Anti-Hallucination System Prompt
    messages = [
        {
            "role": "system",
            "content": "You are the Public Policy Compass AI utilizing RAG. Give accurate, highly concise answers in English based ONLY on the provided context. If the answer cannot be found in the context, explicitly state 'I do not have enough information to answer this based on the provided documents.' Do not invent or hallucinate information."
        },
        {"role": "user", "content": prompt_text}
    ]

    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text], return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            inputs.input_ids,
            max_new_tokens=512, # 🚀 UPGRADE 4: Increased from 200 so it doesn't cut off
            temperature=0.1,    # Lowered slightly to make it more factual, less creative
            repetition_penalty=1.1, # Prevents it from repeating the same sentence
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )

    return tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)

def answer_policy_question(native_question, target_lang="English", simplify=False):
    english_query = translate_fast(native_question, target_lang, "English")

    docs = vector_store.search_documents(english_query, top_k=5)

    if not docs:
        docs_context = "No relevant policies found in Vector DB."
    else:
        docs_context = "\n\n".join([f"Snippet from {d['filename']}:\n{d['content']}" for d in docs])

    prompt = f"Context:\n{docs_context}\n\nQuestion: {english_query}\nAnswer the question using the context. Be direct."
    if simplify:
        prompt += " Simplify the policy language so a middle-school student can immediately understand it."

    eng_ans = generate_english_response(prompt)
    final_ans = translate_fast(eng_ans, "English", target_lang)
    return final_ans, docs

def summarize_document(text, target_lang="English"):
    eng_sum = generate_english_response(f"Summarize this policy into 3 to 5 highly concise, detailed bullet points:\n\n{text[:3000]}")
    return translate_fast(eng_sum, "English", target_lang)