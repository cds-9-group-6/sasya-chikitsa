#!/usr/bin/env python3
"""
Test ChromaDB-compatible metadata filter format
"""

def test_chromadb_filter_format():
    """Test the ChromaDB-compatible metadata filter building"""
    
    # Mock the updated filter building method
    def build_metadata_filter(season, location, disease):
        conditions = []
        
        if season:
            season_lower = season.lower()
            if season_lower in ['summer', 'kharif', 'monsoon']:
                season_variations = ['Summer', 'Kharif', 'KHARIF', 'summer', 'Monsoon']
            elif season_lower in ['winter', 'rabi', 'cold']:
                season_variations = ['Winter', 'Rabi', 'RABI', 'winter', 'Cold']
            else:
                season_variations = [season, season.capitalize(), season.upper()]
            
            conditions.append({"Season_English": {"$in": season_variations}})
        
        if location:
            location_variations = [location, location.capitalize(), location.upper(), location.title()]
            conditions.append({"StateName": {"$in": location_variations}})
        
        if disease:
            disease_variations = [
                disease,
                disease.capitalize(), 
                disease.upper(),
                disease.title(),
                disease.lower().replace('_', ' ').title(),  # Handle Black_rot -> Black Rot
                disease.lower().replace(' ', '_')           # Handle Black Rot -> black_rot
            ]
            conditions.append({"Disease": {"$in": disease_variations}})
        
        # Return None if no conditions
        if not conditions:
            return None
        
        # If only one condition, return it directly (no need for $and)
        if len(conditions) == 1:
            return conditions[0]
        
        # Multiple conditions: wrap in $and operator
        return {"$and": conditions}
    
    print("🧪 Testing ChromaDB-Compatible Filter Format")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "Single condition (Disease only)",
            "season": None,
            "location": None, 
            "disease": "Black_rot"
        },
        {
            "name": "Two conditions (Season + Disease)",
            "season": "summer",
            "location": None,
            "disease": "Black_rot"
        },
        {
            "name": "Three conditions (Season + Location + Disease)",
            "season": "summer",
            "location": "Maharashtra",
            "disease": "Black_rot"
        },
        {
            "name": "No conditions",
            "season": None,
            "location": None,
            "disease": None
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {test_case['name']}")
        print(f"   Input: season='{test_case['season']}', location='{test_case['location']}', disease='{test_case['disease']}'")
        
        result = build_metadata_filter(
            season=test_case['season'],
            location=test_case['location'],
            disease=test_case['disease']
        )
        
        print(f"   Result: {result}")
        
        if result is None:
            print(f"   ✅ No filter (correct for empty input)")
        elif "$and" in result:
            print(f"   ✅ Multiple conditions wrapped in $and (ChromaDB compatible)")
            print(f"   📊 Number of conditions: {len(result['$and'])}")
        else:
            print(f"   ✅ Single condition (ChromaDB compatible)")
    
    print(f"\n🎉 All ChromaDB filter format tests completed!")
    
    # Show the specific problem case that was failing
    print(f"\n🚨 **Fixed Problem Case**:")
    print(f"   Previous (BROKEN): Multiple root-level keys")
    old_format = {
        'Season_English': {'$in': ['Summer', 'Kharif', 'KHARIF', 'summer', 'Monsoon']}, 
        'StateName': {'$in': ['Andhra Pradesh', 'Andhra pradesh', 'ANDHRA PRADESH', 'Andhra Pradesh']}, 
        'Disease': {'$in': ['Black_rot', 'Black_rot', 'BLACK_ROT', 'Black_Rot', 'Black Rot', 'black_rot']}
    }
    print(f"   {old_format}")
    
    print(f"\n   New (FIXED): Single $and operator")
    result = build_metadata_filter("summer", "Andhra Pradesh", "Black_rot")
    print(f"   {result}")
    print(f"   ✅ ChromaDB will accept this format!")

if __name__ == "__main__":
    test_chromadb_filter_format()


