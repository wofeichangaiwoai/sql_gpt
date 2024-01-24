
import torch
from langchain.llms import VLLM
from langchain.llms import HuggingFaceTextGenInference

def get_llm():
    from langchain import LlamaCpp
    import os
    #os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
    llm_type = os.environ.get("LLM_TYPE", None)
    llm_type = llm_type or "tgi"
    print(f"llm_type={llm_type}")
    if torch.cuda.is_available() and llm_type.lower() == "gglm":
        print("There is GPU, LLM is Llama")
        model_path = ""
        n_gpu_layers = 80
        n_batch = 256
        n_ctx = 500
        llm = LlamaCpp(
            model_path=model_path,
            n_gpu_layers=n_gpu_layers,
            n_batch=n_batch,
            n_ctx=n_ctx,
            f16_kv=True,  # MUST set to True, otherwise you will run into problem after a couple of calls
            temperature=0.1,
            verbose=True,
            # cache=True
        )
        return llm
    elif llm_type.lower() == "vllm":
         llm = VLLM( model="NousResearch/Llama-2-13b-chat-hf",
                     trust_remote_code=True,
                     make_new_tokens=250,
                     tensor_parallel_size=2,
                     top_k=10,
                     top_p=0.95,
                     temperature=0.8,
                     tokenizer="hf-internal-testing/llama-tokenizer"
                   )
         return llm
    elif llm_type in ["tgi", "din"]:
        tgi_url = ""
        llm = HuggingFaceTextGenInference(
            inference_server_url=tgi_url,
            max_new_tokens=200,
            top_k=10,
            top_p=0.95,
            typical_p=0.95,
            temperature=0.01,
            repetition_penalty=1.03,
        )
        return llm

llm = get_llm()
