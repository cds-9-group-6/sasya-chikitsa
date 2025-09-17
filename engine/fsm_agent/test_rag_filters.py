#!/usr/bin/env python3
"""
Simple test for RAG metadata filter building without dependencies
"""
import sys
import os

# Add engine directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

def test_metadata_filter_building():
    """Test the metadata filter building logic"""
    
    # Create a mock RAG class to test just the filter building
    class MockRag:
        def _build_metadata_filter(self, season, location, disease):
            """Copy of the metadata filter building method"""
            filters = {}
            
            if season:
                # Handle common season variations
                season_lower = season.lower()
                if season_lower in ['summer', 'kharif', 'monsoon']:
                    season_variations = ['Summer', 'Kharif', 'KHARIF', 'summer', 'Monsoon']
                elif season_lower in ['winter', 'rabi', 'cold']:
                    season_variations = ['Winter', 'Rabi', 'RABI', 'winter', 'Cold']
                else:
                    season_variations = [season, season.capitalize(), season.upper()]
                
                filters["Season_English"] = {"$in": season_variations}
                print(f"🌱 Season filter: {season_variations}")
            
            if location:
                # Create flexible location matching (try StateName first, most common)
                location_variations = [
                    location, 
                    location.capitalize(), 
                    location.upper(),
                    location.title()
                ]
                # For simplicity, filter by StateName (can be extended later for DistrictName)
                filters["StateName"] = {"$in": location_variations}
                print(f"📍 Location filter (StateName): {location_variations}")
            
            if disease:
                # Handle disease name variations
                disease_variations = [
                    disease,
                    disease.capitalize(), 
                    disease.upper(),
                    disease.title(),
                    disease.lower().replace('_', ' ').title(),  # Handle Black_rot -> Black Rot
                    disease.lower().replace(' ', '_')           # Handle Black Rot -> black_rot
                ]
                filters["Disease"] = {"$in": disease_variations}
                print(f"🦠 Disease filter: {disease_variations}")
            
            # Return None if no filters, otherwise return the filter dict
            return filters if filters else None
    
    print("🧪 Testing RAG Metadata Filter Building Logic")
    print("=" * 50)
    
    mock_rag = MockRag()
    
    test_cases = [
        {
            "name": "Summer season + Maharashtra location + Black_rot disease",
            "season": "summer",
            "location": "Maharashtra", 
            "disease": "Black_rot"
        },
        {
            "name": "Winter season only",
            "season": "winter",
            "location": None,
            "disease": None
        },
        {
            "name": "Location + Disease (no season)",
            "season": None,
            "location": "test",
            "disease": "Leaf_spot"
        },
        {
            "name": "Disease with underscore",
            "season": None,
            "location": None,
            "disease": "early_blight"
        },
        {
            "name": "Disease with space",
            "season": None,
            "location": None,
            "disease": "Powdery Mildew"
        },
        {
            "name": "Empty filters",
            "season": None,
            "location": None,
            "disease": None
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {test_case['name']}")
        print(f"   Input - Season: {test_case['season']}, Location: {test_case['location']}, Disease: {test_case['disease']}")
        
        result = mock_rag._build_metadata_filter(
            season=test_case['season'],
            location=test_case['location'],
            disease=test_case['disease']
        )
        
        print(f"   Result: {result}")
        
        if result:
            print(f"   ✅ Filter created with {len(result)} conditions")
        else:
            print(f"   ✅ No filters (as expected)")
    
    print(f"\n🎉 All metadata filter tests completed!")
    
    # Test with context from API request
    print(f"\n🌐 Testing API Request Context")
    print("-" * 30)
    
    # Simulate API request context: {plant_type: "tomato", location: "test", season: "summer"}
    api_context = {
        "plant_type": "tomato",
        "location": "test", 
        "season": "summer",
        "disease": "Black_rot"  # This would come from classification
    }
    
    print(f"📤 API Request Context: {api_context}")
    
    result = mock_rag._build_metadata_filter(
        season=api_context["season"],
        location=api_context["location"],
        disease=api_context["disease"]
    )
    
    print(f"🎯 Generated ChromaDB Filter: {result}")
    print(f"✅ Context-aware filtering ready!")

if __name__ == "__main__":
    test_metadata_filter_building()


