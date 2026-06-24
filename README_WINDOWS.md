# BriefLoop — Executive Prep & Follow-Up Copilot

This project is configured for your setup:

- Streamlit runs in Windows PowerShell.
- vLLM/Qwen runs in WSL.
- The app calls vLLM through the OpenAI-compatible `/v1` API.
- All data is synthetic.

## 1. Open the project folder

In PowerShell:

```powershell
cd "C:\Users\nagababu.andraju\Desktop\My Projects\ceo_meeting_prep_copilot_starter"
```

## 2. Create and activate Python environment

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If activation is blocked:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Confirm data loads

```powershell
python scripts\check_data.py
```

You should see rows loaded for contacts, meetings, inbox, prior_notes, followups, travel, source_docs, and strategic_priorities.

## 5. Start vLLM in WSL

You said you already know how to start your model. The app expects an OpenAI-compatible endpoint like:

```text
http://localhost:8000/v1
```

Your vLLM command should use something equivalent to:

```bash
vllm serve Qwen/Qwen2.5-14B-Instruct --host 0.0.0.0 --port 8000 --api-key local-vllm-key
```

If your model is local, use your local model path.

## 6. Test from PowerShell

With vLLM running in WSL, test from Windows PowerShell:

```powershell
python scripts\test_vllm_connection.py http://localhost:8000/v1 local-vllm-key
```

If `localhost` does not work, get your WSL IP:

```powershell
$wslIp = (wsl hostname -I).Trim().Split(" ")[0]
$wslIp
```

Then test:

```powershell
python scripts\test_vllm_connection.py "http://$wslIp`:8000/v1" local-vllm-key
```

Use that same URL in the Streamlit sidebar.

## 7. Run Streamlit

```powershell
streamlit run app.py
```

Open the local browser URL shown by Streamlit, usually:

```text
http://localhost:8501
```

## 8. First demo

1. Open the Meeting Brief tab.
2. Select `M001 — Donor strategy check-in`.
3. Click `Generate Brief`.
4. Open Follow-Up Extractor.
5. Click `Extract Follow-Ups`.

## 9. Resume wording

Built BriefLoop, a local-first Streamlit prototype for executive meeting prep and follow-up tracking. It uses synthetic executive-operations data and a self-hosted Qwen model through vLLM to generate meeting briefs, surface relationship context and open loops, and extract post-meeting action items with human-review and privacy guardrails.
