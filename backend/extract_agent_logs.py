
import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from sqlmodel import Session, select, col
from app.database import engine
from app.models import AnalysisReport, Company

def extract_logs(report_id: str = None):
    """
    Extracts agent logs from an analysis report and saves them to files.
    """
    print("Connecting to database...")
    
    with Session(engine) as session:
        if report_id:
            report = session.get(AnalysisReport, report_id)
            if not report:
                print(f"Error: Report with ID {report_id} not found.")
                return
        else:
            # Get latest report
            print("Fetching latest report...")
            statement = select(AnalysisReport).order_by(col(AnalysisReport.created_at).desc()).limit(1)
            report = session.exec(statement).first()
            if not report:
                print("Error: No analysis reports found in database.")
                return

        # Get company name for folder
        company = session.get(Company, report.company_id)
        company_name = company.name if company else "Unknown_Company"
        
        # Create directory name
        # Format: [company]_report_[timestamp]
        # Clean company name for filesystem
        safe_company_name = "".join([c for c in company_name if c.isalnum() or c in (' ', '_', '-')]).strip().replace(' ', '_')
        timestamp = report.created_at.strftime("%Y%m%d_%H%M%S")
        folder_name = f"{safe_company_name}_report_{timestamp}"
        
        # Base path: /home/ubuntu/Senti-Mochi/tests/agents_logs
        base_dir = Path("/home/ubuntu/Senti-Mochi/tests/agents_logs")
        target_dir = base_dir / folder_name
        
        print(f"Creating directory: {target_dir}")
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract logs
        agent_logs = report.agent_logs or []
        
        if not agent_logs:
            print("Warning: No agent logs found in this report.")
        
        # Helper to write file
        def write_log(filename, content):
            path = target_dir / filename
            with open(path, "w", encoding="utf-8") as f:
                if isinstance(content, (dict, list)):
                    f.write(json.dumps(content, indent=2, default=str))
                else:
                    f.write(str(content))
            print(f"Saved: {filename}")

        # Process logs
        found_agents = set()
        
        for log in agent_logs:
            agent_name = log.get("agent")
            output = log.get("output")
            found_agents.add(agent_name)
            
            if agent_name == "news":
                # Save News Analysis
                # Check if it's a dict or string
                if isinstance(output, dict):
                    content = output.get("news_analysis", str(output))
                    write_log("news_analysis_report.txt", content)
                    
                    # Also save critique/defense if available
                    if "news_critique" in output:
                        write_log("news_critique.txt", output["news_critique"])
                    if "news_defense" in output:
                         write_log("news_defense.txt", output["news_defense"])
                else:
                    write_log("news_analysis_report.txt", output)

            elif agent_name == "financial":
                # Save Financial Analysis
                if isinstance(output, dict):
                    content = output.get("financial_analysis", str(output))
                    write_log("financial_analysis_report.txt", content)
                     # Also save critique/defense if available
                    if "financial_critique" in output:
                        write_log("financial_critique.txt", output["financial_critique"])
                    if "financial_defense" in output:
                         write_log("financial_defense.txt", output["financial_defense"])
                else:
                    write_log("financial_analysis_report.txt", output)

            elif agent_name == "claims":
                # Save Claims Analysis
                if isinstance(output, dict):
                    content = output.get("claims_analysis", str(output))
                    write_log("claims_analysis_report.txt", content)
                    if "claims_critique" in output:
                        write_log("claims_critique.txt", output["claims_critique"])
                else:
                    write_log("claims_analysis_report.txt", output)

            elif agent_name == "critique":
                # Save Cross-Examination Critiques
                if isinstance(output, dict):
                    if "news_critique" in output:
                        write_log("news_critique.txt", output["news_critique"])
                    if "financial_critique" in output:
                        write_log("financial_critique.txt", output["financial_critique"])
                    if "claims_critique" in output:
                        write_log("claims_critique.txt", output["claims_critique"])
                else:
                    write_log("critique_raw.txt", output)

            elif agent_name == "debate":
                # Save Debate Report
                # Attempt to split if structured
                if isinstance(output, dict):
                    # Save full debate JSON
                    write_log("debate_full_report.json", output)
                    
                    # Try to save legible transcripts
                    transcript = output.get("transcript", "")
                    if transcript:
                        write_log("debate_transcript.txt", transcript)
                        
                    gov = output.get("government_stand", {})
                    if gov:
                         write_log("government_report.txt", json.dumps(gov, indent=2))
                         
                    opp = output.get("opposition_stand", {})
                    if opp:
                         write_log("opposition_report.txt", json.dumps(opp, indent=2))
                else:
                    write_log("debate_report.txt", output)
            
            elif agent_name == "citation_registry":
                 write_log("citation_registry.json", output)
            
            elif agent_name == "market_sentiment":
                 write_log("market_sentiment.json", output)

        # Save Judge Report (from top level report fields)
        judge_content = f"""JUDGE REPORT
Decision: {report.rating}
Confidence: {report.confidence_score}%

SUMMARY:
{report.summary}

BULL CASE:
{report.bull_case}

BEAR CASE:
{report.bear_case}

RISK FACTORS:
{report.risk_factors}

JUSTIFICATION:
{report.justification}
"""
        write_log("judge_report.txt", judge_content)
        print("Saved: judge_report.txt")
        
        print(f"\nAll logs extracted to: {target_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract agent logs from analysis report")
    parser.add_argument("--report-id", help="Specific Report ID to extract", default=None)
    args = parser.parse_args()
    
    extract_logs(args.report_id)
