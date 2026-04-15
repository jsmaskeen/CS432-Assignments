import json

def minify_with_subsections(input_file, output_file):
    with open(input_file, 'r') as f:
        data = json.load(f)

    paths = data.get('paths', {})
    # Using a list of dictionaries for easier LLM parsing
    minified_data = []

    for path, methods in paths.items():
        for method, details in methods.items():
            if method.lower() not in ['get', 'post', 'put', 'delete', 'patch']:
                continue
            
            # Extract subsection from 'tags'; default to 'General' if missing
            tags = details.get('tags', ['General'])
            subsection = tags[0]
            
            minified_data.append({
                "path": path,
                "method": method.upper(),
                "subsection": subsection,
                "required_params": [
                    p.get("name") for p in details.get("parameters", [])
                    if p.get("required") == True
                ]
            })

    with open(output_file, 'w') as f:
        json.dump(minified_data, f, indent=2)
    print(f"Minified file with subsections saved to: {output_file}")

# Usage
minify_with_subsections('openapi.json', 'slim_openapi_subsections.json')
