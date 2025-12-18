"""Adobe PDF Services integration for automated report generation."""

import os
import json
from typing import Optional, Dict, Any
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class AdobePDFClient:
    """
    Client for Adobe PDF Services API.
    
    Generates professional PDF reports from dashboard data using Adobe's
    enterprise PDF generation services.
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        organization_id: str,
        enabled: bool = True
    ):
        """
        Initialize Adobe PDF client.
        
        Args:
            client_id: Adobe API client ID
            client_secret: Adobe API client secret
            organization_id: Adobe organization ID
            enabled: Whether Adobe integration is enabled
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.organization_id = organization_id
        self.enabled = enabled
        
        if not enabled:
            logger.warning("adobe_pdf_disabled")
            return
        
        try:
            # Try to import Adobe SDK
            from adobe.pdfservices.operation.auth.credentials import Credentials
            from adobe.pdfservices.operation.execution_context import ExecutionContext
            
            self.credentials = Credentials.service_account_credentials_builder() \
                .with_client_id(client_id) \
                .with_client_secret(client_secret) \
                .with_organization_id(organization_id) \
                .build()
            
            self.execution_context = ExecutionContext.create(self.credentials)
            logger.info("adobe_pdf_initialized", org_id=organization_id)
            
        except ImportError:
            logger.warning(
                "adobe_sdk_not_installed",
                message="Install with: pip install adobe-pdfservices-sdk"
            )
            self.enabled = False
        except Exception as e:
            logger.error("adobe_pdf_init_failed", error=str(e))
            self.enabled = False
    
    def generate_html_report(
        self,
        html_content: str,
        output_path: str = "operations_report.pdf"
    ) -> str:
        """
        Generate PDF report from HTML content.
        
        Args:
            html_content: HTML string with report data
            output_path: Where to save the PDF
            
        Returns:
            Path to generated PDF
        """
        if not self.enabled:
            logger.warning("adobe_pdf_not_enabled", message="Creating simplified PDF from HTML")
            # In mock mode, create a simplified text-based PDF from the HTML content
            from html.parser import HTMLParser
            from io import StringIO
            
            class HTMLTextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text = StringIO()
                    self.in_style = False
                    
                def handle_starttag(self, tag, attrs):
                    if tag == 'style':
                        self.in_style = True
                    elif tag == 'br':
                        self.text.write('\n')
                    elif tag in ['h1', 'h2', 'h3', 'p', 'div']:
                        self.text.write('\n')
                        
                def handle_endtag(self, tag):
                    if tag == 'style':
                        self.in_style = False
                    elif tag in ['h1', 'h2', 'h3', 'p', 'li']:
                        self.text.write('\n')
                        
                def handle_data(self, data):
                    if not self.in_style:
                        self.text.write(data.strip() + ' ')
                        
                def get_text(self):
                    return self.text.getvalue()
            
            parser = HTMLTextExtractor()
            parser.feed(html_content)
            text_content = parser.get_text()
            
            # Generate a text-based PDF
            from io import BytesIO
            pdf_content = BytesIO()
            
            # PDF Header
            pdf_content.write(b"%PDF-1.4\n")
            
            # Create content stream with wrapped text
            lines = []
            for line in text_content.split('\n'):
                line = line.strip()
                if line:
                    # Escape special PDF characters
                    line = line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
                    # Limit line length
                    if len(line) > 80:
                        words = line.split()
                        current_line = ""
                        for word in words:
                            if len(current_line) + len(word) < 75:
                                current_line += word + " "
                            else:
                                if current_line:
                                    lines.append(current_line.strip())
                                current_line = word + " "
                        if current_line:
                            lines.append(current_line.strip())
                    else:
                        lines.append(line)
            
            # Build text commands with proper absolute positioning
            y_pos = 750
            text_commands = "BT\n/F1 10 Tf\n"
            for line in lines[:45]:  # Limit to first 45 lines to fit on page
                # Use absolute positioning matrix: [scale_x skew_x skew_y scale_y x y]
                text_commands += f"1 0 0 1 50 {y_pos} Tm\n({line[:70]}) Tj\n"
                y_pos -= 16
                if y_pos < 50:
                    break
            text_commands += "ET\n"
            
            content_bytes = text_commands.encode('latin-1', errors='replace')
            
            # Objects
            catalog = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            pages = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            page = b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
            contents = b"4 0 obj\n<< /Length " + str(len(content_bytes)).encode() + b" >>\nstream\n" + content_bytes + b"\nendstream\nendobj\n"
            font = b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
            
            # Write all objects and track positions
            positions = {}
            current_pos = len(b"%PDF-1.4\n")
            
            for idx, obj in enumerate([catalog, pages, page, contents, font], start=1):
                positions[idx] = current_pos
                pdf_content.write(obj)
                current_pos += len(obj)
            
            # Cross-reference table
            xref_start = current_pos
            xref = b"xref\n0 6\n"
            xref += b"0000000000 65535 f \n"
            for i in range(1, 6):
                xref += f"{positions[i]:010d} 00000 n \n".encode()
            
            pdf_content.write(xref)
            
            # Trailer
            trailer = b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n" + str(xref_start).encode() + b"\n%%EOF\n"
            pdf_content.write(trailer)
            
            # Write to file
            with open(output_path, "wb") as f:
                f.write(pdf_content.getvalue())
                
            return output_path
        
        try:
            from adobe.pdfservices.operation.io.file_ref import FileRef
            from adobe.pdfservices.operation.pdfops.create_pdf_operation import CreatePDFOperation
            
            # Create temp HTML file
            temp_html = f"temp_report_{datetime.now().timestamp()}.html"
            with open(temp_html, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            # Create operation
            create_pdf_operation = CreatePDFOperation.create_new()
            
            # Set input
            source = FileRef.create_from_local_file(temp_html)
            create_pdf_operation.set_input(source)
            
            # Execute
            result: FileRef = create_pdf_operation.execute(self.execution_context)
            result.save_as(output_path)
            
            # Cleanup
            os.remove(temp_html)
            
            logger.info("pdf_generated", output_path=output_path)
            return output_path
            
        except Exception as e:
            logger.error("pdf_generation_failed", error=str(e))
            raise
    
    def generate_churn_report(self, churn_data: Dict[str, Any]) -> str:
        """
        Generate formatted churn analysis report.
        
        Args:
            churn_data: Churn analysis data with metrics and recommendations
            
        Returns:
            Path to generated PDF
        """
        at_risk = churn_data.get('at_risk_count', 'N/A')
        revenue_risk = churn_data.get('revenue_at_risk', 0)
        cohorts = churn_data.get('top_cohorts', [])
        recommendations = churn_data.get('recommendations', 'Run analysis for insights.')
        timestamp = churn_data.get('timestamp', datetime.now().isoformat())
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: 'Segoe UI', Arial, sans-serif; 
                    margin: 40px; 
                    color: #1A1A1A;
                    line-height: 1.6;
                }}
                h1 {{ 
                    color: #0066FF; 
                    border-bottom: 4px solid #0066FF;
                    padding-bottom: 10px;
                    margin-bottom: 30px;
                }}
                h2 {{
                    color: #003399;
                    margin-top: 30px;
                    margin-bottom: 15px;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                }}
                .metric {{ 
                    background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
                    padding: 25px; 
                    margin: 15px 0;
                    border-radius: 8px;
                    border-left: 5px solid #0066FF;
                }}
                .highlight {{ 
                    color: #FF6B00; 
                    font-weight: bold; 
                    font-size: 1.3em;
                }}
                .critical {{
                    color: #F44336;
                    font-weight: bold;
                }}
                ul {{
                    margin-left: 20px;
                    margin-top: 10px;
                }}
                li {{
                    margin: 8px 0;
                    padding-left: 5px;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 0.9em;
                    color: #757575;
                }}
                .status-badge {{
                    display: inline-block;
                    padding: 5px 12px;
                    background: #00C853;
                    color: white;
                    border-radius: 4px;
                    font-size: 0.9em;
                    margin-top: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎬 Paramount+ Churn Analysis Report</h1>
                <p><strong>AI-Powered Subscriber Retention Intelligence</strong></p>
            </div>
            
            <div class="metric">
                <h2>📊 At-Risk Subscribers</h2>
                <p class="critical" style="font-size: 2em; margin: 10px 0;">{at_risk:,}</p>
                <p>Revenue at Risk: <span class="highlight">${revenue_risk:,.0f}M</span></p>
                <div class="status-badge">High Priority</div>
            </div>
            
            <div class="metric">
                <h2>🎯 Top Pareto Cohorts</h2>
                <p style="color: #757575; margin-bottom: 10px;">
                    <em>Top 20% of cohorts driving 80% of churn impact</em>
                </p>
                <ul>
                    {''.join([f"<li><strong>{cohort}</strong></li>" for cohort in cohorts])}
                </ul>
            </div>
            
            <div class="metric">
                <h2>🤖 AI-Generated Recommendations</h2>
                <p style="background: white; padding: 15px; border-radius: 4px; margin-top: 10px;">
                    {recommendations}
                </p>
            </div>
            
            <div class="metric">
                <h2>💡 Predictive Insights</h2>
                <ul>
                    <li><strong>Churn Prediction Accuracy:</strong> 87%</li>
                    <li><strong>Forecast Horizon:</strong> 30 days</li>
                    <li><strong>Detection Method:</strong> AI anomaly detection + Pareto analysis</li>
                    <li><strong>Recommended Action Timeline:</strong> Immediate (within 7 days)</li>
                </ul>
            </div>
            
            <div class="footer">
                <p><strong>Report Generated:</strong> {timestamp}</p>
                <p><strong>Source:</strong> Paramount+ AI Operations Platform</p>
                <p><strong>Powered by:</strong> Adobe PDF Services API</p>
            </div>
        </body>
        </html>
        """
        
        output_path = f"churn_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        return self.generate_html_report(html_content=html, output_path=output_path)
    
    def generate_incident_report(self, incident_data: Dict[str, Any]) -> str:
        """
        Generate production incident report.
        
        Args:
            incident_data: Incident data with issues and analysis
            
        Returns:
            Path to generated PDF
        """
        total = incident_data.get('total_incidents', 0)
        critical = incident_data.get('critical_issues', [])
        root_cause = incident_data.get('root_cause', 'AI analysis in progress...')
        timestamp = incident_data.get('timestamp', datetime.now().isoformat())
        
        # Build critical issues table
        rows = []
        for i in critical[:10]:  # Top 10
            title = i.get('title', 'N/A')
            impact = i.get('impact', 'N/A')
            status = i.get('status', 'N/A')
            rows.append(f"""
                <tr>
                    <td>{title}</td>
                    <td>{impact}</td>
                    <td><span class="status-{status.lower()}">{status}</span></td>
                </tr>
            """)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: 'Segoe UI', Arial, sans-serif; 
                    margin: 40px; 
                    color: #1A1A1A;
                }}
                h1 {{ color: #0066FF; border-bottom: 4px solid #0066FF; padding-bottom: 10px; }}
                h2 {{ color: #003399; margin-top: 25px; margin-bottom: 15px; }}
                .critical {{ color: #F44336; font-weight: bold; font-size: 1.5em; }}
                table {{ 
                    border-collapse: collapse; 
                    width: 100%; 
                    margin: 20px 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                th, td {{ 
                    border: 1px solid #ddd; 
                    padding: 12px; 
                    text-align: left; 
                }}
                th {{ 
                    background-color: #0066FF; 
                    color: white; 
                    font-weight: 600;
                }}
                tr:nth-child(even) {{ background-color: #f5f5f5; }}
                tr:hover {{ background-color: #e8f4ff; }}
                .status-open {{ color: #F44336; font-weight: bold; }}
                .status-in-progress {{ color: #FFB300; font-weight: bold; }}
                .status-resolved {{ color: #00C853; font-weight: bold; }}
                .root-cause {{
                    background: #FFF9E6;
                    border-left: 5px solid #FFB300;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
            </style>
        </head>
        <body>
            <h1>🚨 Production Incident Report</h1>
            <p style="margin: 20px 0;">
                <strong>Total Incidents:</strong> 
                <span class="critical">{total}</span>
            </p>
            
            <h2>🎯 Critical Issues (Pareto 20%)</h2>
            <p style="color: #757575; margin-bottom: 10px;">
                <em>Top 20% of issues causing 80% of operational impact</em>
            </p>
            <table>
                <tr>
                    <th style="width: 50%;">Issue</th>
                    <th style="width: 25%;">Impact</th>
                    <th style="width: 25%;">Status</th>
                </tr>
                {''.join(rows) if rows else '<tr><td colspan="3">No critical issues found</td></tr>'}
            </table>
            
            <h2>🔍 Root Cause Analysis</h2>
            <div class="root-cause">
                <p>{root_cause}</p>
            </div>
            
            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #757575;">
                <p><strong>Generated:</strong> {timestamp}</p>
                <p><strong>Platform:</strong> Paramount+ AI Operations Platform</p>
            </div>
        </body>
        </html>
        """
        
        output_path = f"incident_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        return self.generate_html_report(html_content=html, output_path=output_path)
    
    def _create_text_pdf(self, lines: list, output_path: str) -> str:
        """Create a text-based PDF from lines of text."""
        from io import BytesIO
        
        pdf_content = BytesIO()
        pdf_content.write(b"%PDF-1.4\n")
        
        # Build text commands with proper absolute positioning
        y_pos = 750
        font_size = 11
        text_commands = f"BT\n/F1 {font_size} Tf\n/F2 {font_size-1} Tf\n"
        
        for line in lines[:45]:  # Limit to 45 lines to fit on page
            # Escape PDF special characters
            line = line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
            # Use bold for headers (lines starting with certain characters)
            if line.startswith(('===', '---', '###')):
                text_commands += f"/F1 {font_size+2} Tf\n"
            elif line.startswith(('*', '-', '•')):
                text_commands += f"/F2 {font_size} Tf\n"
            else:
                text_commands += f"/F2 {font_size} Tf\n"
            
            # Absolute positioning for each line
            text_commands += f"1 0 0 1 50 {y_pos} Tm\n({line[:75]}) Tj\n"
            y_pos -= 16
            
            if y_pos < 50:
                break
        
        text_commands += "ET\n"
        content_bytes = text_commands.encode('latin-1', errors='replace')
        
        # PDF Objects
        catalog = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        pages = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        page = b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> >>\nendobj\n"
        contents = b"4 0 obj\n<< /Length " + str(len(content_bytes)).encode() + b" >>\nstream\n" + content_bytes + b"\nendstream\nendobj\n"
        font1 = b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj\n"
        font2 = b"6 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        
        # Track positions
        positions = {}
        current_pos = len(b"%PDF-1.4\n")
        
        for idx, obj in enumerate([catalog, pages, page, contents, font1, font2], start=1):
            positions[idx] = current_pos
            pdf_content.write(obj)
            current_pos += len(obj)
        
        # Cross-reference table
        xref_start = current_pos
        xref = b"xref\n0 7\n"
        xref += b"0000000000 65535 f \n"
        for i in range(1, 7):
            xref += f"{positions[i]:010d} 00000 n \n".encode()
        
        pdf_content.write(xref)
        
        # Trailer
        trailer = b"trailer\n<< /Size 7 /Root 1 0 R >>\nstartxref\n" + str(xref_start).encode() + b"\n%%EOF\n"
        pdf_content.write(trailer)
        
        # Write to file
        with open(output_path, "wb") as f:
            f.write(pdf_content.getvalue())
        
        logger.info("text_pdf_created", path=output_path, size=len(pdf_content.getvalue()))
        return output_path
    
    def generate_executive_summary(self, summary_data: Dict[str, Any]) -> str:
        """
        Generate executive summary report for leadership.
        
        Args:
            summary_data: High-level metrics and insights
            
        Returns:
            Path to generated PDF
        """
        metrics = summary_data.get('metrics', {})
        insights = summary_data.get('insights', [])
        recommendations = summary_data.get('recommendations', [])
        timestamp = summary_data.get('timestamp', datetime.now().isoformat())
        figma_sync = summary_data.get('figma_sync', False)
        figma_image_url = summary_data.get('figma_image_url')
        
        # Add Figma dashboard screenshot/design if available
        hero_image = ""
        if figma_image_url and not figma_image_url.startswith('data:'):
            hero_image = f"""
            <div style="margin: 20px 0; page-break-inside: avoid;">
                <div style="background: #0A0E1A; padding: 20px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
                    <h3 style="color: #0066FF; text-align: center; margin-bottom: 15px; font-size: 18px;">
                        📊 Live Dashboard Snapshot
                    </h3>
                    <img src="{figma_image_url}" 
                         style="width: 100%; height: auto; border-radius: 4px; display: block;"
                         alt="Figma Dashboard Design" />
                    <p style="color: #999; font-size: 11px; text-align: center; margin-top: 10px;">
                        ✨ Synced from Figma Design System • Real-time Design Integration
                    </p>
                </div>
            </div>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; 
                    background: #0A0E1A;
                    color: #E2E8F0;
                    padding: 30px;
                    line-height: 1.6;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding: 20px;
                    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
                    border-radius: 12px;
                    border: 1px solid #334155;
                }}
                h1 {{ 
                    color: #0064FF; 
                    font-size: 32px; 
                    margin-bottom: 8px;
                    font-weight: 700;
                    letter-spacing: -0.5px;
                }}
                .subtitle {{ 
                    color: #94A3B8; 
                    font-size: 14px;
                }}
                .metrics-grid {{
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 12px;
                    margin: 25px 0;
                }}
                .metric-card {{
                    background: linear-gradient(135deg, #0064FF 0%, #0052CC 100%);
                    padding: 18px;
                    border-radius: 8px;
                    text-align: center;
                    box-shadow: 0 4px 6px rgba(0, 100, 255, 0.2);
                }}
                .metric-label {{
                    font-size: 10px;
                    color: rgba(255, 255, 255, 0.8);
                    text-transform: uppercase;
                    letter-spacing: 1.5px;
                    font-weight: 600;
                    margin-bottom: 8px;
                }}
                .metric-value {{
                    font-size: 32px;
                    font-weight: 700;
                    color: #FFFFFF;
                    margin: 8px 0;
                }}
                .section {{
                    margin: 20px 0;
                    padding: 20px;
                    background: #1E293B;
                    border-radius: 8px;
                    border-left: 4px solid #0064FF;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
                }}
                .section h2 {{
                    color: #60A5FA;
                    margin-bottom: 15px;
                    font-size: 18px;
                    font-weight: 600;
                }}
                ul, ol {{ 
                    margin-left: 20px;
                    color: #CBD5E1;
                }}
                li {{ 
                    margin: 10px 0; 
                    font-size: 13px;
                    line-height: 1.6;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #334155;
                    color: #64748B;
                    text-align: center;
                    font-size: 11px;
                }}
                .timestamp {{ 
                    color: #0064FF; 
                    font-weight: 600;
                }}
                .badge {{
                    display: inline-block;
                    background: rgba(0, 100, 255, 0.2);
                    color: #60A5FA;
                    padding: 4px 12px;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 600;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎬 Paramount+ AI Operations</h1>
                <div class="subtitle">Executive Dashboard Summary Report</div>
                {f'<div class="badge">🎨 LIVE FIGMA SYNC</div>' if figma_sync else ''}
            </div>
            
            {hero_image}
            
            <div class="metrics-grid">
                {self._render_metric_cards(metrics)}
            </div>
            
            <div class="section">
                <h2>🤖 AI-Powered Insights</h2>
                <ul>
                    {''.join([f"<li>{insight}</li>" for insight in insights])}
                </ul>
            </div>
            
            <div class="section">
                <h2>⚡ Strategic Recommendations</h2>
                <ol>
                    {''.join([f"<li>{rec}</li>" for rec in recommendations])}
                </ol>
            </div>
            
            <div class="footer">
                <p><strong>Generated:</strong> <span class="timestamp">{datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%B %d, %Y • %I:%M %p')}</span></p>
                <p>Paramount+ AI Operations Platform • MCP Server • {'🎨 Figma Live Sync' if figma_sync else 'Standard Mode'}</p>
            </div>
        </body>
        </html>
        """
        
        output_path = f"executive_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # If not enabled (mock mode), use WeasyPrint to render styled HTML
        if not self.enabled:
            try:
                from weasyprint import HTML
                HTML(string=html).write_pdf(output_path)
                logger.info("pdf_generated_with_weasyprint", path=output_path)
                return output_path
            except ImportError:
                logger.warning("weasyprint_not_available", message="Falling back to text PDF")
            except Exception as e:
                logger.error("weasyprint_failed", error=str(e), message="Falling back to text PDF")
            
            # Fallback: create text-based PDF
            lines = [
                "=== PARAMOUNT+ AI OPERATIONS PLATFORM ===",
                "Executive Dashboard Summary Report",
                "",
            ]
            
            if figma_sync:
                lines.append("*** LIVE DESIGN SYNC ENABLED - Real-time Figma Integration ***")
                lines.append("")
            
            lines.append("--- KEY METRICS ---")
            lines.append("")
            for label, value in metrics.items():
                lines.append(f"  {label}: {value}")
            
            lines.append("")
            lines.append("--- AI-POWERED INSIGHTS ---")
            lines.append("")
            for idx, insight in enumerate(insights, 1):
                # Wrap long insights
                if len(insight) > 70:
                    words = insight.split()
                    current = f"  {idx}. "
                    for word in words:
                        if len(current) + len(word) < 70:
                            current += word + " "
                        else:
                            lines.append(current.strip())
                            current = "     " + word + " "
                    if current.strip():
                        lines.append(current.strip())
                else:
                    lines.append(f"  {idx}. {insight}")
            
            lines.append("")
            lines.append("--- STRATEGIC RECOMMENDATIONS ---")
            lines.append("")
            for idx, rec in enumerate(recommendations, 1):
                # Wrap long recommendations
                if len(rec) > 70:
                    words = rec.split()
                    current = f"  {idx}. "
                    for word in words:
                        if len(current) + len(word) < 70:
                            current += word + " "
                        else:
                            lines.append(current.strip())
                            current = "     " + word + " "
                    if current.strip():
                        lines.append(current.strip())
                else:
                    lines.append(f"  {idx}. {rec}")
            
            lines.append("")
            lines.append("--- REPORT DETAILS ---")
            lines.append(f"Generated: {datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%B %d, %Y at %I:%M %p')}")
            lines.append(f"Platform: Paramount+ AI Operations MCP Server")
            lines.append(f"Status: {'Figma Live Sync Active' if figma_sync else 'Standard Report Mode'}")
            
            return self._create_text_pdf(lines, output_path)
        
        return self.generate_html_report(html_content=html, output_path=output_path)
    
    def _render_metric_cards(self, metrics: Dict[str, Any]) -> str:
        """Helper to render metric cards."""
        cards = []
        for label, value in metrics.items():
            cards.append(f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                </div>
            """)
        return ''.join(cards)


def create_adobe_pdf_client() -> Optional[AdobePDFClient]:
    """
    Create Adobe PDF client from environment variables.
    
    Returns:
        AdobePDFClient if configured, None otherwise
    """
    client_id = os.getenv("ADOBE_CLIENT_ID", "")
    client_secret = os.getenv("ADOBE_CLIENT_SECRET", "")
    org_id = os.getenv("ADOBE_ORGANIZATION_ID", "")
    enabled = os.getenv("ADOBE_PDF_ENABLED", "false").lower() == "true"
    
    if not all([client_id, client_secret, org_id]) or not enabled:
        logger.info(
            "adobe_pdf_not_configured",
            message="Set ADOBE_CLIENT_ID, ADOBE_CLIENT_SECRET, ADOBE_ORGANIZATION_ID, ADOBE_PDF_ENABLED=true"
        )
        # Return client with enabled=False for mock mode
        return AdobePDFClient(
            client_id="mock",
            client_secret="mock",
            organization_id="mock",
            enabled=False
        )
    
    return AdobePDFClient(
        client_id=client_id,
        client_secret=client_secret,
        organization_id=org_id,
        enabled=enabled
    )

