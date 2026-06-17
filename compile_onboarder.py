import json
import sys
import os

def load_json_config(config_path):
    if not os.path.exists(config_path):
        print(f"Error: Config file not found at {config_path}")
        return None
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def compile_template(template_path, config, output_path):
    if not os.path.exists(template_path):
        print(f"Error: Template not found at {template_path}")
        return False
        
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()
        
    # Replace all double-bracket tokens with values from JSON config
    compiled_content = template_content
    for key, value in config.items():
        token = f"{{{{{key.upper()}}}}}"
        compiled_content = compiled_content.replace(token, str(value))
        
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(compiled_content)
        
    print(f"✔ Successfully compiled and generated HTML page at: {output_path}")
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 compile_onboarder.py <config_json_path> [output_html_path]")
        sys.exit(1)
        
    config_path = sys.argv[1]
    config = load_json_config(config_path)
    if not config:
        sys.exit(1)
        
    # Default outputs path resolution (assuming template is in root)
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        company_clean = config.get("company_name", "output").lower().replace(" ", "_")
        output_path = f"{company_clean}_demo.html"
        
    # Template resides in root
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "elvity_onboarding_template.html")
    compile_template(template_path, config, output_path)

if __name__ == "__main__":
    main()
