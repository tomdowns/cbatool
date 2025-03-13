"""
Standardized Report Generator for CBAtool v2.0

Provides a flexible reporting mechanism for all types of cable analysis.
"""

import os
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Add openpyxl imports for formatting
try:
	import openpyxl
	from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
	OPENPYXL_AVAILABLE = True
except ImportError:
	OPENPYXL_AVAILABLE = False
	logger.warning("openpyxl styles not available - Excel formatting will be limited")

try:
	from reportlab.lib.pagesizes import A4
	from reportlab.lib import colors
	from reportlab.lib.units import inch
	from reportlab.lib.units import cm
	from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
	from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
	REPORTLAB_AVAILABLE = True
except ImportError:
	REPORTLAB_AVAILABLE = False
	logger.warning("ReportLab is not installed. PDF generation will not be available.")

class ReportGenerator:
	"""
	Centralized report generation class for cable analysis.
	
	Works with any analyzer type (depth, position, combined) to produce
	consistent reports in multiple formats (Excel, PDF, HTML visualization).
	
	Attributes:
		output_directory (str): Directory where reports will be saved
		report_paths (Dict[str, str]): Dictionary of generated report paths
		report_config (Dict[str, Any]): Configuration for report generation
	"""
	
	def __init__(self, output_directory: str, report_config: Optional[Dict[str, Any]] = None):
		"""
		Initialize the ReportGenerator.
		
		Args:
			output_directory: Directory where reports will be saved
			report_config: Optional configuration dictionary for report generation
		"""
		self.output_directory = output_directory
		
		# Ensure output directory exists
		os.makedirs(output_directory, exist_ok=True)
		
		# Initialize report paths dictionary
		self.report_paths = {}
		
		# Set default report configuration if none provided
		self.report_config = report_config or {
			'include_anomalies': True,
			'include_problem_sections': True,
			'include_summary': True,
			'include_recommendations': True,
			'company_name': '',
			'project_name': '',
			'client_name': '',
			'regulatory_requirements': ''
		}
		
		# Logging setup
		logger.info(f"ReportGenerator initialized. Output directory: {output_directory}")
	
	def generate_reports(self, analysis_results: Dict[str, Any], 
						 visualization_path: Optional[str] = None,
						 analysis_type: str = 'combined') -> Dict[str, str]:
		"""
		Generate a complete set of reports from analysis results.
		
		This is the main entry point for report generation. It will produce:
		- Excel report with comprehensive data
		- PDF summary report
		- Links to visualization files
		
		Args:
			analysis_results: Dictionary containing analysis results from any analyzer
			visualization_path: Optional path to HTML visualization file
			analysis_type: Type of analysis ('depth', 'position', or 'combined')
			
		Returns:
			Dictionary of generated report paths
		"""
		# Validate input
		if not analysis_results:
			logger.warning("No analysis results provided for report generation")
			return {}
			
		# Normalize analysis results to standard format
		standardized_results = self._standardize_analysis_results(analysis_results, analysis_type)
		
		# Generate individual Excel reports
		excel_reports = self._generate_excel_reports(standardized_results, analysis_type)
		
		# Consolidate Excel reports if we have any
		consolidated_excel_path = ""
		if excel_reports:
			consolidated_excel_path = self.consolidate_excel_reports(
				excel_reports, 
				f"{analysis_type}_analysis_report.xlsx"
			)
		
		# Generate PDF summary
		pdf_path = self.generate_pdf_summary(
			standardized_results, 
			visualization_path,
			f"{analysis_type}_analysis_summary.pdf"
		)
		
		# Collect and return all report paths
		report_paths = {
			'excel': consolidated_excel_path,
			'pdf': pdf_path,
			'visualization': visualization_path,
			'individual_reports': excel_reports
		}
		
		# Store report paths for later reference
		self.report_paths = report_paths
		
		return report_paths
	
	def _standardize_analysis_results(self, analysis_results: Dict[str, Any], 
									 analysis_type: str) -> Dict[str, Any]:
		"""
		Standardize analysis results to a consistent format.
		
		This ensures that regardless of analyzer type, we have a consistent
		structure for report generation.
		
		Args:
			analysis_results: Raw analysis results from an analyzer
			analysis_type: Type of analysis ('depth', 'position', or 'combined')
			
		Returns:
			Standardized analysis results dictionary
		"""
		standardized = {
			'analysis_type': analysis_type,
			'timestamp': datetime.now(),
			'summary': {},
			'problem_sections': {},
			'anomalies': {},
			'recommendations': []
		}
		
		# Extract common fields from analysis_results
		if 'analysis_complete' in analysis_results:
			standardized['analysis_complete'] = analysis_results['analysis_complete']
			
		# Process depth analysis results
		if analysis_type in ['depth', 'combined']:
			self._extract_depth_results(analysis_results, standardized)
			
		# Process position analysis results
		if analysis_type in ['position', 'combined']:
			self._extract_position_results(analysis_results, standardized)
			
		# Generate recommendations based on analysis results
		standardized['recommendations'] = self._generate_recommendations(standardized)
		
		return standardized
	
	def _extract_depth_results(self, analysis_results: Dict[str, Any], 
							  standardized: Dict[str, Any]) -> None:
		"""
		Extract and standardize depth analysis results.
		
		Args:
			analysis_results: Raw analysis results
			standardized: Standardized results to update
		"""
		# Extract summary information
		if 'compliance_percentage' in analysis_results:
			standardized['summary']['depth_compliance_percentage'] = analysis_results['compliance_percentage']
			
		if 'target_depth' in analysis_results:
			standardized['summary']['target_depth'] = analysis_results['target_depth']
			
		# Extract problem sections
		if 'problem_sections' in analysis_results:
			problem_sections = analysis_results['problem_sections']
			if isinstance(problem_sections, pd.DataFrame) and not problem_sections.empty:
				standardized['problem_sections']['depth'] = problem_sections
				
				# Extract counts by severity if available
				if 'section_count' in analysis_results:
					standardized['summary']['depth_problem_section_count'] = analysis_results['section_count']
					
				if 'total_problem_length' in analysis_results:
					standardized['summary']['depth_total_problem_length'] = analysis_results['total_problem_length']
		
		# Extract anomalies
		if 'anomalies' in analysis_results:
			anomalies = analysis_results['anomalies']
			if isinstance(anomalies, pd.DataFrame) and not anomalies.empty:
				standardized['anomalies']['depth'] = anomalies
				
				# Add anomaly count to summary
				standardized['summary']['depth_anomaly_count'] = len(anomalies)
	
	def _extract_position_results(self, analysis_results: Dict[str, Any], 
								 standardized: Dict[str, Any]) -> None:
		"""
		Extract and standardize position analysis results.
		
		Args:
			analysis_results: Raw analysis results
			standardized: Standardized results to update
		"""
		# Check for position_analysis section in combined results
		position_results = (analysis_results 
			if self.report_config.get('analysis_type') == 'position' 
			else analysis_results.get('position_analysis', {}))
  
		problem_key = 'problem_sections' if 'problem_sections' in position_results else 'problem_segments'
		problem_data = position_results.get(problem_key)
		
		# Handle problem sections data if it exists and is not empty
		if problem_data is not None and isinstance(problem_data, pd.DataFrame) and not problem_data.empty:
			standardized['problem_sections']['position'] = problem_data
			
		# Extract summary information from position results or nested summary
		position_summary = position_results.get('summary', {})
		if position_summary:
			# Add relevant fields to standardized summary
			for key, value in position_summary.items():
				if not isinstance(value, dict):  # Skip nested dictionaries
					standardized['summary'][f'position_{key}'] = value
			
			# Handle nested anomalies dictionary
			if 'anomalies' in position_summary:
				standardized['summary']['position_anomalies'] = position_summary['anomalies']
		
		# Extract problem sections (might be called problem_sections or problem_segments)
		if 'problem_sections' in position_results:
			sections = position_results['problem_sections']
			if isinstance(sections, pd.DataFrame) and not sections.empty:
				standardized['problem_sections']['position'] = sections
		elif 'problem_segments' in position_results:
			segments = position_results['problem_segments']
			if isinstance(segments, pd.DataFrame) and not segments.empty:
				standardized['problem_sections']['position'] = segments
		
		# Extract position anomalies
		# Position anomalies are often detected points rather than a separate DataFrame
		position_data = position_results.get('position_analysis', None)
		if position_data is not None and isinstance(position_data, pd.DataFrame):
			# Filter anomalous points based on common position anomaly flags
			anomaly_flags = [
				'Is_KP_Jump', 'Is_KP_Reversal', 'Is_KP_Duplicate', 
				'Is_Significant_Deviation'
			]
			
			# Check which flags exist in the DataFrame
			existing_flags = [flag for flag in anomaly_flags if flag in position_data.columns]
			
			if existing_flags:
				# Create a combined filter for any anomaly
				anomaly_filter = False
				for flag in existing_flags:
					anomaly_filter |= position_data[flag]
				
				# Extract anomalous points
				position_anomalies = position_data[anomaly_filter].copy()
				
				if not position_anomalies.empty:
					standardized['anomalies']['position'] = position_anomalies
					standardized['summary']['position_anomaly_count'] = len(position_anomalies)
	
	def _generate_recommendations(self, standardized_results: Dict[str, Any]) -> List[Dict[str, Any]]:
		"""
		Generate recommendations based on standardized analysis results.
		
		Args:
			standardized_results: Standardized analysis results
			
		Returns:
			List of recommendation dictionaries
		"""
		recommendations = []
		
		# Helper function to add a recommendation
		def add_recommendation(category, severity, description, action):
			recommendations.append({
				'category': category,
				'severity': severity,
				'description': description,
				'action': action
			})
		
		# Depth analysis recommendations
		if 'depth' in standardized_results.get('problem_sections', {}):
			depth_sections = standardized_results['problem_sections']['depth']
			
			if isinstance(depth_sections, pd.DataFrame) and not depth_sections.empty and 'Severity' in depth_sections.columns:
				# Check for high severity sections
				high_severity = depth_sections[depth_sections['Severity'] == 'High']
				if not high_severity.empty:
					add_recommendation(
						'Depth', 'High',
						f"Found {len(high_severity)} high severity burial depth issues",
						"Remedial burial required for these sections"
					)
				
				# Check for medium severity sections
				medium_severity = depth_sections[depth_sections['Severity'] == 'Medium']
				if not medium_severity.empty:
					add_recommendation(
						'Depth', 'Medium',
						f"Found {len(medium_severity)} medium severity burial depth issues",
						"Consider additional protection for these sections"
					)
				
				# Check for low severity sections
				low_severity = depth_sections[depth_sections['Severity'] == 'Low']
				if not low_severity.empty:
					add_recommendation(
						'Depth', 'Low',
						f"Found {len(low_severity)} low severity burial depth issues",
						"Monitor these sections during maintenance"
					)
		
		# Position analysis recommendations
		if 'position' in standardized_results.get('problem_sections', {}):
			position_sections = standardized_results['problem_sections']['position']
			
			if isinstance(position_sections, pd.DataFrame) and not position_sections.empty:
				# Check if severity is available
				if 'Severity' in position_sections.columns:
					# Generate recommendations by severity
					for severity in ['High', 'Medium', 'Low']:
						severity_sections = position_sections[position_sections['Severity'] == severity]
						if not severity_sections.empty:
							add_recommendation(
								'Position', severity,
								f"Found {len(severity_sections)} {severity.lower()} severity position issues",
								"Review position data quality in these sections"
							)
				else:
					# Generic recommendation if severity not available
					add_recommendation(
						'Position', 'Medium',
						f"Found {len(position_sections)} position quality issues",
						"Review position data quality in problem sections"
					)
		
		# Check for specific position anomaly types
		position_anomalies = standardized_results.get('summary', {}).get('position_anomalies', {})
		if position_anomalies:
			if position_anomalies.get('kp_jumps', 0) > 0:
				add_recommendation(
					'Position', 'Medium',
					f"Found {position_anomalies['kp_jumps']} KP jumps",
					"Investigate KP continuity issues"
				)
			
			if position_anomalies.get('kp_reversals', 0) > 0:
				add_recommendation(
					'Position', 'High',
					f"Found {position_anomalies['kp_reversals']} KP reversals",
					"Review position data sequence and direction"
				)
		
		return recommendations
		
	def _generate_excel_reports(self, standardized_results: Dict[str, Any], 
							   analysis_type: str) -> Dict[str, str]:
		"""
		Generate individual Excel reports from standardized analysis results.
		
		Args:
			standardized_results: Standardized analysis results
			analysis_type: Type of analysis ('depth', 'position', or 'combined')
			
		Returns:
			Dictionary mapping report names to file paths
		"""
		excel_reports = {}
		
		# Generate problem sections reports
		for section_type, sections_df in standardized_results.get('problem_sections', {}).items():
			if isinstance(sections_df, pd.DataFrame) and not sections_df.empty:
				report_name = f"{section_type}_problem_sections"
				file_path = os.path.join(self.output_directory, f"{report_name}.xlsx")
				
				# Save to Excel
				sections_df.to_excel(file_path, index=False)
				
				# Add to report dictionary
				excel_reports[f"{section_type.capitalize()} Problem Sections"] = file_path
		
		# Generate anomalies reports
		for anomaly_type, anomalies_df in standardized_results.get('anomalies', {}).items():
			if isinstance(anomalies_df, pd.DataFrame) and not anomalies_df.empty:
				report_name = f"{anomaly_type}_anomalies"
				file_path = os.path.join(self.output_directory, f"{report_name}.xlsx")
				
				# Save to Excel
				anomalies_df.to_excel(file_path, index=False)
				
				# Add to report dictionary
				excel_reports[f"{anomaly_type.capitalize()} Anomalies"] = file_path
		
		# Generate recommendations report
		recommendations = standardized_results.get('recommendations', [])
		if recommendations:
			report_name = "recommendations"
			file_path = os.path.join(self.output_directory, f"{report_name}.xlsx")
			
			# Convert to DataFrame
			recommendations_df = pd.DataFrame(recommendations)
			
			# Save to Excel
			recommendations_df.to_excel(file_path, index=False)
			
			# Add to report dictionary
			excel_reports["Recommendations"] = file_path
		
		# Generate summary report
		summary = standardized_results.get('summary', {})
		if summary:
			report_name = "analysis_summary"
			file_path = os.path.join(self.output_directory, f"{report_name}.xlsx")
			
			# Convert to DataFrame (two columns: Metric and Value)
			summary_rows = []
			for key, value in summary.items():
				if not isinstance(value, dict):  # Skip nested dictionaries
					summary_rows.append({
						'Metric': key.replace('_', ' ').title(),
						'Value': value
					})
			
			summary_df = pd.DataFrame(summary_rows)
			
			# Save to Excel
			summary_df.to_excel(file_path, index=False)
			
			# Add to report dictionary
			excel_reports["Analysis Summary"] = file_path
		
		return excel_reports
	
	def consolidate_excel_reports(self, 
								 reports: Dict[str, str], 
								 output_filename: str = 'comprehensive_analysis_report.xlsx') -> str:
		"""
		Consolidate multiple Excel reports into a single workbook.
		
		Args:
			reports: Dictionary mapping report names to file paths
			output_filename: Name of the output consolidated report
		
		Returns:
			Path to the consolidated Excel report
		"""
		# Validate input
		if not reports:
			logger.warning("No reports provided for consolidation")
			return ""
		
		# Full output path
		output_path = os.path.join(self.output_directory, output_filename)
		
		try:
			# Create Excel writer
			with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
				# First add a summary sheet
				summary_data = self._create_summary_sheet(reports)
				summary_data.to_excel(writer, sheet_name='Summary', index=False)
				
				# Add recommendations sheet if it exists
				if "Recommendations" in reports:
					try:
						recommendations_df = pd.read_excel(reports["Recommendations"])
						recommendations_df.to_excel(writer, sheet_name='Recommendations', index=False)
						
						# Apply formatting to recommendations
						self._apply_excel_formatting(writer, 'Recommendations', recommendations_df, 
												   format_type='recommendations')
					except Exception as e:
						logger.error(f"Error adding recommendations: {e}")
				
				# Add each report
				for report_name, report_path in reports.items():
					# Skip recommendations as we've already added it
					if report_name == "Recommendations":
						continue
						
					# Validate report exists
					if not os.path.exists(report_path):
						logger.warning(f"Report not found: {report_path}")
						continue
					
					# Read Excel file
					try:
						xls = pd.ExcelFile(report_path)
						
						# Add each sheet to the consolidated workbook
						for sheet_name in xls.sheet_names:
							# Create a better sheet name
							friendly_sheet_name = f"{report_name}"
							if len(friendly_sheet_name) > 31:  # Excel sheet name length limit
								friendly_sheet_name = friendly_sheet_name[:31]
							
							# Read and write sheet
							df = pd.read_excel(report_path, sheet_name=sheet_name)
							df.to_excel(writer, sheet_name=friendly_sheet_name, index=False)
							
							# Apply formatting if possible
							self._apply_excel_formatting(writer, friendly_sheet_name, df)
					except Exception as e:
						logger.error(f"Error processing report {report_name}: {e}")
				
				# Add project information sheet
				self._add_project_info_sheet(writer)
			
			logger.info(f"Consolidated report created: {output_path}")
			self.report_paths['excel'] = output_path
			return output_path
		
		except Exception as e:
			logger.error(f"Error consolidating reports: {e}")
			return ""

	def generate_pdf_summary(self, standardized_results: Dict[str, Any], 
							visualization_path: Optional[str] = None,
							output_filename: str = 'analysis_summary.pdf') -> str:
		"""
		Generate a PDF summary report from analysis results.
		
		Args:
			standardized_results: Standardized analysis results
			visualization_path: Optional path to visualization file
			output_filename: Name of the output PDF file
			
		Returns:
			Path to the generated PDF file or empty string if generation failed
		"""
		# Skip PDF generation if ReportLab is not available
		if not REPORTLAB_AVAILABLE:
			logger.warning("ReportLab not available - skipping PDF generation")
			return ""
		
		output_path = os.path.join(self.output_directory, output_filename)
		
		try:
			# Create PDF document
			doc = SimpleDocTemplate(
				output_path,
				pagesize=A4,
				rightMargin=72,
				leftMargin=72,
				topMargin=72,
				bottomMargin=72
			)
			
			# Initialize story (content elements)
			story = []
			
			# Get styles
			styles = getSampleStyleSheet()
			title_style = styles['Title']
			heading_style = styles['Heading1']
			subheading_style = styles['Heading2']
			normal_style = styles['Normal']
			
			# Add custom style for section headers
			section_style = ParagraphStyle(
				'SectionStyle',
				parent=styles['Heading2'],
				backColor=colors.lightgrey,
				borderPadding=5,
			)
			
			# Add title
			project_name = self.report_config.get('project_name', 'Cable Analysis Report')
			story.append(Paragraph(project_name, title_style))
			story.append(Spacer(1, 0.25 * inch))
			
			# Add report info
			now = datetime.now().strftime("%Y-%m-%d %H:%M")
			story.append(Paragraph(f"Report Generated: {now}", normal_style))
			
			if self.report_config.get('client_name'):
				story.append(Paragraph(f"Client: {self.report_config['client_name']}", normal_style))
				
			if self.report_config.get('company_name'):
				story.append(Paragraph(f"Company: {self.report_config['company_name']}", normal_style))
			
			story.append(Spacer(1, 0.25 * inch))
			
			# Add summary section
			story.append(Paragraph("Analysis Summary", heading_style))
			story.append(Spacer(1, 0.1 * inch))
			
			summary = standardized_results.get('summary', {})
			
			# Create summary table data
			summary_data = [['Metric', 'Value']]
			
			for key, value in summary.items():
				if isinstance(value, dict):
					continue  # Skip nested dictionaries
				
				# Format the key for display
				display_key = key.replace('_', ' ').title()
				
				# Format value based on type
				if isinstance(value, float):
					display_value = f"{value:.2f}"
				elif isinstance(value, tuple) and len(value) == 2:
					display_value = f"{value[0]} - {value[1]}"
				else:
					display_value = str(value)
					
				summary_data.append([display_key, display_value])
			
			# Create table
			if len(summary_data) > 1:
				summary_table = Table(summary_data, colWidths=[doc.width * 0.6, doc.width * 0.4])
				summary_table.setStyle(TableStyle([
					('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
					('TEXTCOLOR', (0, 0), (1, 0), colors.black),
					('ALIGN', (0, 0), (1, 0), 'CENTER'),
					('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
					('BOTTOMPADDING', (0, 0), (1, 0), 12),
					('BACKGROUND', (0, 1), (-1, -1), colors.white),
					('GRID', (0, 0), (-1, -1), 1, colors.black),
					('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
				]))
				story.append(summary_table)
				story.append(Spacer(1, 0.25 * inch))
			else:
				story.append(Paragraph("No summary data available.", normal_style))
				story.append(Spacer(1, 0.25 * inch))
			
			# Add problem sections if available
			problem_sections = standardized_results.get('problem_sections', {})
			if problem_sections:
				story.append(Paragraph("Problem Sections", heading_style))
				story.append(Spacer(1, 0.1 * inch))
				
				for section_type, sections in problem_sections.items():
					if isinstance(sections, pd.DataFrame) and not sections.empty:
						story.append(Paragraph(f"{section_type.title()} Problem Sections", subheading_style))
						story.append(Paragraph(f"Found {len(sections)} problem sections.", normal_style))
						
						# Count by severity if available
						if 'Severity' in sections.columns:
							severity_counts = sections['Severity'].value_counts().to_dict()
							severity_text = ", ".join([f"{count} {severity}" for severity, count in severity_counts.items()])
							story.append(Paragraph(f"Severity distribution: {severity_text}", normal_style))
						
						story.append(Spacer(1, 0.15 * inch))
			
			# Add recommendations if available
			recommendations = standardized_results.get('recommendations', [])
			if recommendations:
				story.append(Paragraph("Recommendations", heading_style))
				story.append(Spacer(1, 0.1 * inch))
				
				for i, rec in enumerate(recommendations):
					category = rec.get('category', 'General')
					severity = rec.get('severity', 'Medium')
					description = rec.get('description', '')
					action = rec.get('action', '')
					
					# Create colored bullet based on severity
					if severity == 'High':
						bullet_color = colors.red
					elif severity == 'Medium':
						bullet_color = colors.orange
					else:
						bullet_color = colors.green
					
					bullet = f'<font color="{bullet_color}">\u2022</font>'
					
					# Add recommendation with colored bullet
					story.append(Paragraph(f"{bullet} <b>{category} ({severity}):</b> {description}", normal_style))
					if action:
						story.append(Paragraph(f"   Action: {action}", normal_style))
					
					story.append(Spacer(1, 0.1 * inch))
			
			# Add information about visualization
			if visualization_path and os.path.exists(visualization_path):
				story.append(Paragraph("Visualization", heading_style))
				story.append(Spacer(1, 0.1 * inch))
				story.append(Paragraph(
					f"An interactive visualization is available at: {os.path.basename(visualization_path)}",
					normal_style
				))
				
				# Could add a static image of the visualization here if available
				# This would require capturing a screenshot of the visualization
			
			# Add regulatory requirements if specified
			if self.report_config.get('regulatory_requirements'):
				story.append(Spacer(1, 0.25 * inch))
				story.append(Paragraph("Regulatory Requirements", heading_style))
				story.append(Spacer(1, 0.1 * inch))
				story.append(Paragraph(self.report_config['regulatory_requirements'], normal_style))
			
			# Build the PDF
			doc.build(story)
			logger.info(f"PDF summary report created: {output_path}")
			return output_path
			
		except Exception as e:
			logger.error(f"Error generating PDF summary: {str(e)}")
			return ""
	
	def _create_summary_sheet(self, reports: Dict[str, str]) -> pd.DataFrame:
		"""
		Create a summary sheet for the consolidated report.
		
		Args:
			reports: Dictionary mapping report names to file paths
		
		Returns:
			DataFrame with summary information
		"""
		summary_rows = []
		
		# Add report information
		for report_name, report_path in reports.items():
			if os.path.exists(report_path):
				try:
					xls = pd.ExcelFile(report_path)
					total_rows = 0
					
					# Count total rows across all sheets
					for sheet_name in xls.sheet_names:
						df = pd.read_excel(report_path, sheet_name=sheet_name)
						total_rows += len(df)
					
					summary_rows.append({
						'Report Type': report_name,
						'File': os.path.basename(report_path),
						'Sheets': len(xls.sheet_names),
						'Total Rows': total_rows,
						'Date Generated': datetime.fromtimestamp(os.path.getmtime(report_path)).strftime('%Y-%m-%d %H:%M')
					})
				except Exception as e:
					logger.error(f"Error analyzing report {report_name}: {e}")
					summary_rows.append({
						'Report Type': report_name,
						'File': os.path.basename(report_path),
						'Sheets': 'Error',
						'Total Rows': 'Error',
						'Date Generated': datetime.fromtimestamp(os.path.getmtime(report_path)).strftime('%Y-%m-%d %H:%M')
					})
		
		# Add timestamp and metadata
		metadata = [{
			'Report Type': 'METADATA',
			'File': 'N/A',
			'Sheets': 'N/A',
			'Total Rows': 'N/A',
			'Date Generated': datetime.now().strftime('%Y-%m-%d %H:%M')
		}]
		
		return pd.DataFrame(metadata + summary_rows)
	
	def _add_project_info_sheet(self, writer):
		"""
		Add a project information sheet to the Excel report.
		
		Args:
			writer: Excel writer object
		"""
		# Create project info
		project_info = [
			{'Field': 'Project Name', 'Value': self.report_config.get('project_name', '')},
			{'Field': 'Client Name', 'Value': self.report_config.get('client_name', '')},
			{'Field': 'Company Name', 'Value': self.report_config.get('company_name', '')},
			{'Field': 'Report Generated', 'Value': datetime.now().strftime('%Y-%m-%d %H:%M')},
			{'Field': 'Regulatory Requirements', 'Value': self.report_config.get('regulatory_requirements', '')}
		]
		
		# Convert to DataFrame
		df = pd.DataFrame(project_info)
		
		# Write to Excel
		df.to_excel(writer, sheet_name='Project Information', index=False)
		
		# Apply formatting
		if OPENPYXL_AVAILABLE:
			try:
				worksheet = writer.sheets['Project Information']
				
				# Format headers
				for cell in worksheet["A1:B1"]:
					for c in cell:
						c.font = Font(bold=True)
						c.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
				
				# Auto-fit columns
				for idx, col in enumerate(['A', 'B']):
					max_length = 0
					for cell in worksheet[col]:
						try:
							if len(str(cell.value)) > max_length:
								max_length = len(str(cell.value))
						except:
							pass
					adjusted_width = (max_length + 2)
					worksheet.column_dimensions[col].width = adjusted_width
			except Exception as e:
				logger.warning(f"Error formatting project info sheet: {e}")
	
	def _apply_excel_formatting(self, writer, sheet_name, df, format_type='default'):
		"""
		Apply formatting to Excel worksheet.
		
		Args:
			writer: Excel writer object
			sheet_name: Name of the sheet to format
			df: DataFrame containing the data
			format_type: Type of formatting to apply ('default', 'recommendations', etc.)
		"""
		try:
			# Only proceed if openpyxl is available
			if not OPENPYXL_AVAILABLE:
				return
				
			# Get the workbook and worksheet
			workbook = writer.book
			worksheet = writer.sheets[sheet_name]
			
			# Auto-fit columns
			for idx, col in enumerate(df.columns):
				# Calculate max width
				max_len = max(
					df[col].astype(str).map(len).max(),
					len(str(col))
				) + 2  # Add a little extra space
				
				# Set column width (using Excel column letters A, B, C...)
				col_letter = chr(65 + idx) if idx < 26 else chr(64 + idx // 26) + chr(65 + idx % 26)
				worksheet.column_dimensions[col_letter].width = min(max_len, 40)
			
			# Format header row
			for cell in worksheet["1:1"]:
				cell.font = Font(bold=True)
				cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
			
			# Apply specific formatting based on format_type
			if format_type == 'recommendations':
				self._format_recommendations(worksheet, df)
			elif 'Severity' in df.columns:
				self._format_severity_column(worksheet, df)
			
		except Exception as e:
			# Don't let formatting errors prevent report generation
			logger.warning(f"Error applying Excel formatting: {e}")
	
	def _format_severity_column(self, worksheet, df):
		"""
		Format the Severity column with color coding.
		
		Args:
			worksheet: Excel worksheet
			df: DataFrame containing the data
		"""
		# Find the severity column
		severity_col_idx = list(df.columns).index('Severity')
		severity_col_letter = chr(65 + severity_col_idx) if severity_col_idx < 26 else chr(64 + severity_col_idx // 26) + chr(65 + severity_col_idx % 26)
		
		# Apply formatting to each cell in the severity column
		for row_idx, severity in enumerate(df['Severity'], start=2):  # Start from row 2 (after header)
			cell = worksheet[f"{severity_col_letter}{row_idx}"]
			
			if severity == 'High':
				cell.fill = PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid')
			elif severity == 'Medium':
				cell.fill = PatternFill(start_color='FFEECC', end_color='FFEECC', fill_type='solid')
			elif severity == 'Low':
				cell.fill = PatternFill(start_color='EEFFCC', end_color='EEFFCC', fill_type='solid')
	
	def _format_recommendations(self, worksheet, df):
		"""
		Format the recommendations sheet with color coding and proper alignment.
		
		Args:
			worksheet: Excel worksheet
			df: DataFrame containing recommendations
		"""
		# Find the category and severity columns
		category_col_idx = list(df.columns).index('category') if 'category' in df.columns else -1
		severity_col_idx = list(df.columns).index('severity') if 'severity' in df.columns else -1
		
		if category_col_idx >= 0:
			category_col_letter = chr(65 + category_col_idx) if category_col_idx < 26 else chr(64 + category_col_idx // 26) + chr(65 + category_col_idx % 26)
			
			# Apply formatting to category cells
			for row_idx, category in enumerate(df['category'], start=2):
				cell = worksheet[f"{category_col_letter}{row_idx}"]
				cell.font = Font(bold=True)
		
		if severity_col_idx >= 0:
			severity_col_letter = chr(65 + severity_col_idx) if severity_col_idx < 26 else chr(64 + severity_col_idx // 26) + chr(65 + severity_col_idx % 26)
			
			# Apply formatting to severity cells
			for row_idx, severity in enumerate(df['severity'], start=2):
				cell = worksheet[f"{severity_col_letter}{row_idx}"]
				
				if severity == 'High':
					cell.fill = PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid')
				elif severity == 'Medium':
					cell.fill = PatternFill(start_color='FFEECC', end_color='FFEECC', fill_type='solid')
				elif severity == 'Low':
					cell.fill = PatternFill(start_color='EEFFCC', end_color='EEFFCC', fill_type='solid')
		
		# Apply borders to all cells
		thin_border = Border(
			left=Side(style='thin'), 
			right=Side(style='thin'), 
			top=Side(style='thin'), 
			bottom=Side(style='thin')
		)
		
		for row in worksheet.iter_rows(min_row=1, max_row=len(df) + 1, min_col=1, max_col=len(df.columns)):
			for cell in row:
				cell.border = thin_border