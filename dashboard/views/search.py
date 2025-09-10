from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from ..models import QueryCache
from ..utils.similarity import QuestionSimilarity
from ..utils.weaviate_client import WeaviateClient
from ..utils.ai_client import AIClient

@login_required
@csrf_exempt
def search_query(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        question = data.get('question', '').strip()
        ai_provider = data.get('ai_provider', 'openai')
        
        if not question:
            return JsonResponse({'error': 'Question is required'}, status=400)
        
        # Check for similar questions
        similarity_checker = QuestionSimilarity()
        cached_queries = QueryCache.objects.values_list('question', flat=True)
        
        similar_idx, similarity_score = similarity_checker.find_similar_question(
            question, list(cached_queries)
        )
        
        if similar_idx is not None:
            # Return cached response
            cached_query = QueryCache.objects.all()[similar_idx]
            return JsonResponse({
                'response': cached_query.response,
                'cached': True,
                'similarity': similarity_score
            })
        
        # Process new query with AI
        try:
            weaviate_client = WeaviateClient()
            ai_client = AIClient(provider=ai_provider)
            
            # Search Weaviate for relevant documents
            search_results = weaviate_client.search(question)
            
            # Generate AI response
            response = ai_client.generate_response(question, search_results)
            
            # Cache the response
            QueryCache.objects.create(
                question=question,
                response=response,
                user=request.user
            )
            
            return JsonResponse({
                'response': response,
                'cached': False
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return render(request, 'dashboard/search.html')
