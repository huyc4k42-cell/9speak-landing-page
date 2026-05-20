import base64

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = 'src="data:image/png;base64,'
end_marker = '"'

start_idx = content.find(start_marker)
if start_idx != -1:
    start_idx += len(start_marker)
    end_idx = content.find(end_marker, start_idx)
    b64_data = content[start_idx:end_idx]
    
    with open('hero-banner-new.png', 'wb') as f:
        f.write(base64.b64decode(b64_data))
        
    new_content = content[:start_idx - len(start_marker)] + 'src="hero-banner-new.png"' + content[end_idx+1:]
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Extracted base64 successfully.")
else:
    print("Base64 string not found.")
