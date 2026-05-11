"""Analytics service for v2 emotional graph.

Provides FeelFlow (time series) and FeelMap (composition) data.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v2 import Feeling


class AnalyticsService:
    """Service for emotional analytics endpoints."""
    
    # Emotion colors for response
    EMOTION_COLORS = {
        "joy": "#FFD93D",
        "sadness": "#6B9FFF",
        "anger": "#FF6B6B",
        "fear": "#B794F4",
        "disgust": "#6BCB77",
    }
    
    @staticmethod
    async def get_feel_flow(
        db: AsyncSession,
        user_id: str,
        entity_id: Optional[str] = None,
        time_bucket: str = "day",
        days: int = 30,
    ) -> Dict:
        """Get time series emotional data for FeelFlow page."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Build query for feelings
        query = select(Feeling).where(
            Feeling.user_id == user_id,
            Feeling.occurred_at >= start_date,
            Feeling.occurred_at <= end_date,
        )
        
        result = await db.execute(query)
        feelings = list(result.scalars().all())
        
        # Group by time bucket
        data_points: Dict[str, Dict] = {}
        
        for feeling in feelings:
            # Extract date key based on time bucket
            if time_bucket == "day":
                date_key = feeling.occurred_at.strftime("%Y-%m-%d")
            elif time_bucket == "week":
                date_key = feeling.occurred_at.strftime("%Y-W%W")
            else:  # month
                date_key = feeling.occurred_at.strftime("%Y-%m")
            
            if date_key not in data_points:
                data_points[date_key] = {"date": date_key, "joy": 0.0, "sadness": 0.0, "anger": 0.0, "fear": 0.0, "disgust": 0.0}
            
            # Add intensity to emotion total
            emotion = feeling.primary_emotion
            if emotion in data_points[date_key]:
                data_points[date_key][emotion] = float(data_points[date_key][emotion]) + float(feeling.intensity)
        
        # Calculate totals
        emotion_totals = {"joy": 0.0, "sadness": 0.0, "anger": 0.0, "fear": 0.0, "disgust": 0.0}
        total_intensity = 0.0
        
        for dp in data_points.values():
            for emotion in emotion_totals:
                val = dp.get(emotion, 0.0)
                emotion_totals[emotion] += float(val)
                total_intensity += float(val)
        
        avg_intensity = total_intensity / len(feelings) if feelings else 0.0
        
        # Sort data points by date
        sorted_data = sorted(data_points.values(), key=lambda x: x["date"])
        
        return {
            "data": sorted_data,
            "time_bucket": time_bucket,
            "emotion_totals": emotion_totals,
            "average_intensity": round(float(avg_intensity), 2),
        }
    
    @staticmethod
    async def get_feel_map(
        db: AsyncSession,
        user_id: str,
        days: int = 30,
    ) -> Dict:
        """Get emotional composition data for FeelMap treemap."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        result = await db.execute(
            select(Feeling).where(
                Feeling.user_id == user_id,
                Feeling.occurred_at >= start_date,
                Feeling.occurred_at <= end_date,
            )
        )
        feelings = list(result.scalars().all())
        
        # Group by emotion - don't access relationships during iteration
        emotion_groups: Dict[str, Dict] = {}
        
        for feeling in feelings:
            emotion = feeling.primary_emotion
            if emotion not in emotion_groups:
                emotion_groups[emotion] = {
                    "emotion": emotion,
                    "color": AnalyticsService.EMOTION_COLORS.get(emotion, "#888888"),
                    "total_weight": 0.0,
                    "feelings": [],
                }
            
            emotion_groups[emotion]["total_weight"] = float(emotion_groups[emotion]["total_weight"]) + float(feeling.intensity)
            # Don't access feeling.entities here - causes async lazy load error
            emotion_groups[emotion]["feelings"].append({
                "label": feeling.label,
                "weight": float(feeling.intensity),
                "about": "",  # Entity info would require separate eager load
                "intensity": float(feeling.intensity),
            })
        
        # Sort groups by total weight
        groups = sorted(emotion_groups.values(), key=lambda x: -x["total_weight"])
        
        # Find dominant emotion
        dominant = groups[0]["emotion"] if groups else "joy"
        
        total_intensity = sum(float(f.intensity) for f in feelings)
        avg_intensity = total_intensity / len(feelings) if feelings else 0.0
        
        return {
            "emotion_groups": groups,
            "dominant_emotion": dominant,
            "total_feelings": len(feelings),
            "average_intensity": round(float(avg_intensity), 2),
        }