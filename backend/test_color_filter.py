"""
Test color filtering functionality
"""
import requests

API_URL = "http://localhost:8000"

def test_color_search(query: str):
    """Test search with color"""
    print(f"\n{'='*60}")
    print(f"🔍 Testing: '{query}'")
    print('='*60)
    
    response = requests.post(
        f"{API_URL}/search/intelligent",
        data={"query": query, "top_k": 10}
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"✅ Search successful")
        print(f"   Query: {data.get('query')}")
        print(f"   Color filter: {data.get('color_filter')}")
        print(f"   Total results: {data.get('total_results')}")
        
        results = data.get('accurate_results', [])
        
        if results:
            print(f"\n📊 Results:")
            for i, result in enumerate(results[:10], 1):
                color = result.get('color', 'unknown')
                name = result.get('name', '')
                score = result.get('score', 0)
                
                # Check if color matches
                query_lower = query.lower()
                color_match = "✅" if query.split()[0].lower() in color.lower() else "❌"
                
                print(f"   {i}. {color_match} {name} (color: {color}, score: {score:.1%})")
            
            # Summary
            expected_color = query.split()[0].lower()
            matching = sum(1 for r in results if expected_color in r.get('color', '').lower())
            total = len(results)
            
            print(f"\n📈 Color match rate: {matching}/{total} ({matching/total*100:.0f}%)")
            
            if matching < total * 0.5:
                print(f"   ⚠️ Less than 50% match the requested color!")
                print(f"   Problem: Color filtering might not be working correctly")
        else:
            print(f"   ⚠️ No results found")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    # Test various color searches
    test_queries = [
        "black table",
        "white chair",
        "brown bed",
        "gray sofa",
        "red table",
        "blue chair"
    ]
    
    for query in test_queries:
        test_color_search(query)
    
    print("\n" + "="*60)
    print("📋 SUMMARY")
    print("="*60)
    print("If you see ❌ marks, the color filtering isn't working correctly.")
    print("Expected: All results should match the requested color.")
    print("\nCommon issues:")
    print("1. Color detection not extracting color from query")
    print("2. product_matches_color() not filtering correctly")
    print("3. Products don't have accurate 'baseColour' field")
    print("="*60)