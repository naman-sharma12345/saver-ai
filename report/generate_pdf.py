"""
Combines 3 HTML report parts into a single PDF.
Uses pdfkit (wkhtmltopdf wrapper) or falls back to weasyprint.

Usage:
    pip install pdfkit
    Then download wkhtmltopdf from https://wkhtmltopdf.org/downloads.html
    OR
    pip install weasyprint
    
    python generate_pdf.py
"""

import os
import sys

REPORT_DIR = os.path.dirname(os.path.abspath(__file__))
PARTS = ['part1.html', 'part2.html', 'part3.html']
OUTPUT = os.path.join(REPORT_DIR, '..', 'SaverAI_Project_Report.pdf')

def combine_html():
    """Read all parts and combine into one HTML string."""
    combined = ""
    for i, part in enumerate(PARTS):
        path = os.path.join(REPORT_DIR, part)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if i == 0:
            # First part: keep everything
            # Remove closing </body></html>
            content = content.replace('</body>', '').replace('</html>', '')
            combined += content
        elif i == len(PARTS) - 1:
            # Last part: keep closing tags, remove opening
            content = content.split('<body>')[1] if '<body>' in content else content
            combined += '\n<div class="page-break"></div>\n' + content
        else:
            # Middle parts: remove both opening and closing
            if '<body>' in content:
                content = content.split('<body>')[1]
            content = content.replace('</body>', '').replace('</html>', '')
            combined += '\n<div class="page-break"></div>\n' + content
    
    return combined

def try_pdfkit(html_content):
    """Try generating PDF using pdfkit (wkhtmltopdf)."""
    import pdfkit
    
    options = {
        'page-size': 'A4',
        'margin-top': '18mm',
        'margin-right': '15mm',
        'margin-bottom': '18mm',
        'margin-left': '15mm',
        'encoding': 'UTF-8',
        'enable-local-file-access': '',
        'print-media-type': '',
        'no-outline': None,
    }
    
    pdfkit.from_string(html_content, OUTPUT, options=options)
    return True

def try_weasyprint(html_content):
    """Try generating PDF using weasyprint."""
    from weasyprint import HTML
    HTML(string=html_content).write_pdf(OUTPUT)
    return True

def try_browser_print(combined_html_path):
    """Fallback: save combined HTML and instruct user to print from browser."""
    print(f"\n📄 Combined HTML saved to: {combined_html_path}")
    print("   Open this file in Chrome/Edge and press Ctrl+P → Save as PDF")
    return False

def main():
    print("📝 SaverAI Project Report Generator")
    print("=" * 40)
    
    # Combine HTML parts
    print("🔗 Combining HTML parts...")
    combined = combine_html()
    
    # Save combined HTML (always useful as backup)
    combined_path = os.path.join(REPORT_DIR, 'combined_report.html')
    with open(combined_path, 'w', encoding='utf-8') as f:
        f.write(combined)
    print(f"   ✅ Combined HTML saved: combined_report.html")
    
    # Try PDF generation methods
    print("\n🖨️  Generating PDF...")
    
    # Method 1: pdfkit
    try:
        if try_pdfkit(combined):
            print(f"   ✅ PDF generated successfully: {os.path.basename(OUTPUT)}")
            print(f"   📁 Location: {OUTPUT}")
            return
    except ImportError:
        print("   ⚠️  pdfkit not installed (pip install pdfkit)")
    except Exception as e:
        print(f"   ⚠️  pdfkit failed: {e}")
    
    # Method 2: weasyprint
    try:
        if try_weasyprint(combined):
            print(f"   ✅ PDF generated successfully: {os.path.basename(OUTPUT)}")
            print(f"   📁 Location: {OUTPUT}")
            return
    except ImportError:
        print("   ⚠️  weasyprint not installed (pip install weasyprint)")
    except Exception as e:
        print(f"   ⚠️  weasyprint failed: {e}")
    
    # Method 3: Browser fallback
    print("\n" + "=" * 40)
    print("🌐 FALLBACK: Open the combined HTML in your browser to print as PDF:")
    print(f"   File: {combined_path}")
    print("   Steps: Open in Chrome → Ctrl+P → Destination: Save as PDF → Save")
    
    # Try to auto-open in browser
    try:
        import webbrowser
        webbrowser.open(f'file:///{combined_path.replace(os.sep, "/")}')
        print("   ✅ Opened in your default browser!")
    except:
        pass

if __name__ == '__main__':
    main()
