# ML-Based AI Chatbot Architecture Plan

## Project Overview
Build an intelligent AI chatbot that can answer career-related questions using Machine Learning (NLP) techniques.

## Current State Analysis
- Existing chatbot uses simple keyword matching
- Limited to predefined responses
- Only handles MPSC, UPSC, Army queries
- No ML capabilities

## Proposed ML-Based Solution

### Option 1: TF-IDF + Cosine Similarity (Recommended)
```
User Query → TF-IDF Vectorization → Compare with FAQ Database → Return Best Match
```
- **Pros**: Fast, works offline, no API needed
- **Cons**: Limited understanding of context

### Option 2: Simple Neural Network (Text Classification)
```
User Query → Word Embeddings → Dense Layers → Intent Classification → Response Generation
```
- **Pros**: Learns patterns, can handle variations
- **Cons**: Needs training data

### Option 3: Pre-trained Model API (Ollama/Llama)
```
User Query → Ollama API → LLM Response
```
- **Pros**: Most intelligent, handles any question
- **Cons**: Requires local Ollama installation or internet

## Recommended Architecture

### Phase 1: Enhanced Keyword + ML Hybrid
1. Expand knowledge base with 500+ Q&A pairs
2. Use TF-IDF for semantic matching
3. Add fallback to rule-based for common queries

### Phase 2: Intent Classification
1. Train classifier to identify user intent
2. Categories: exam_info, career_guidance, salary, courses, colleges, general

### Phase 3: Full LLM Integration
1. Integrate Ollama for free local AI
2. Or use sentence-transformers for semantic search

## Implementation Steps

### Step 1: Create Knowledge Base
- Collect 500+ career-related Q&A in English, Hindi, Marathi
- Categories: Exams, Careers, Courses, Colleges, Salary, Jobs

### Step 2: Build ML Pipeline
- Use TF-IDF Vectorizer
- Implement cosine similarity matching
- Add intent detection

### Step 3: API Integration
- Create `/api/chat` endpoint
- Handle multilingual input
- Return structured responses

### Step 4: Frontend Enhancement
- Improve chat UI
- Add typing indicators
- Add quick reply buttons

## Files to Modify
1. `app.py` - Add ML endpoints and logic
2. `templates/chat.html` - Enhance UI
3. `data/knowledge_base.json` - Store Q&A

## Success Metrics
- Answer coverage: 90%+ of career questions
- Response accuracy: >85%
- Multi-language support: EN, HI, MR
