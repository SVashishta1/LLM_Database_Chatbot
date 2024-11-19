---
title: LLM Database Chatbot
emoji: 🏃
colorFrom: red
colorTo: red
sdk: gradio
sdk_version: "5.0.1"
app_file: app.py
pinned: false
license: mit
short_description: A chatbot for database analysis powered by LLM via Groq API.
app_type: tabular
inference: true
---

# LLM Database Chatbot

This project provides an interactive Gradio-based chatbot that lets users ask questions about their uploaded CSV data in plain English. It generates appropriate SQL queries to analyze the data and returns insightful, natural-language answers.

# Working
- Upload a CSV file.
- Ask questions about the data (e.g., "When is the busiest time in the day?").
- The chatbot translates questions into SQL queries, executes them on the data, and returns a detailed response.

# Tools & Libraries 
- Gradio for the User Interface
- Groq API to access LLMs
- LangChain for cordination between the components in the pipeline
- SQLite for storing and retrieving the data
