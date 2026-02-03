from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import permissions
from .collaborative_filtering import get_collaborative_filtering_recommendations
from django.contrib.auth import get_user_model

User = get_user_model()


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def collaborative_recommendations(request):
    """
    获取协同过滤推荐
    """
    user_id = request.user.id
    
    try:
        recommendations = get_collaborative_filtering_recommendations(user_id)
        return Response(recommendations)
    except Exception as e:
        return Response({
            'error': f'获取推荐失败: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def health_risk_prediction(request):
    """
    健康风险预测
    """
    user_id = request.user.id
    
    try:
        from .collaborative_filtering import HealthCollaborativeFiltering
        
        cf = HealthCollaborativeFiltering()
        cf.build_user_profiles()
        
        risk_predictions = cf.predict_health_risk(user_id)
        
        return Response({
            'risk_predictions': risk_predictions,
            'risk_level': calculate_overall_risk_level(risk_predictions)
        })
    except Exception as e:
        return Response({
            'error': f'风险预测失败: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def personalized_recommendations(request):
    """
    个性化健康建议
    """
    user_id = request.user.id
    
    try:
        from .collaborative_filtering import HealthCollaborativeFiltering
        
        cf = HealthCollaborativeFiltering()
        cf.build_user_profiles()
        
        recommendations = cf.generate_health_recommendations(user_id)
        
        return Response({
            'recommendations': recommendations,
            'total_count': len(recommendations)
        })
    except Exception as e:
        return Response({
            'error': f'获取建议失败: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def early_warning_alerts(request):
    """
    早期预警提醒
    """
    user_id = request.user.id
    
    try:
        from .collaborative_filtering import HealthCollaborativeFiltering
        
        cf = HealthCollaborativeFiltering()
        cf.build_user_profiles()
        
        alerts = cf.get_early_warning_alerts(user_id)
        
        return Response({
            'alerts': alerts,
            'total_alerts': len(alerts),
            'high_priority_alerts': len([a for a in alerts if a.get('severity') == 'high'])
        })
    except Exception as e:
        return Response({
            'error': f'获取预警失败: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def similar_users_health_data(request):
    """
    相似用户的健康数据对比
    """
    user_id = request.user.id
    
    try:
        from .collaborative_filtering import HealthCollaborativeFiltering
        
        cf = HealthCollaborativeFiltering()
        cf.build_user_profiles()
        
        similar_users = cf.find_similar_users(user_id, top_k=5)
        
        # 获取相似用户的详细健康数据
        similar_users_data = []
        for similar_user_id, similarity in similar_users:
            if similar_user_id in cf.health_profiles:
                profile = cf.health_profiles[similar_user_id]
                similar_users_data.append({
                    'user_id': similar_user_id,
                    'username': profile['username'],
                    'similarity': round(similarity, 3),
                    'health_metrics': profile['health_metrics'],
                    'risk_factors': profile['risk_factors'],
                    'lifestyle_score': profile['lifestyle_score']
                })
        
        return Response({
            'similar_users': similar_users_data,
            'target_user_profile': cf.health_profiles.get(user_id, {})
        })
    except Exception as e:
        return Response({
            'error': f'获取相似用户数据失败: {str(e)}'
        }, status=500)


def calculate_overall_risk_level(risk_predictions):
    """计算总体风险等级"""
    if not risk_predictions:
        return 'low'
    
    max_probability = max(risk_predictions.values())
    
    if max_probability > 0.7:
        return 'high'
    elif max_probability > 0.4:
        return 'medium'
    else:
        return 'low'
