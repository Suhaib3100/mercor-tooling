"""
Webhook Server for Airtable Automations
Receives webhooks from Airtable and triggers the pipeline
"""

from flask import Flask, request, jsonify
import json
import threading
from src.airtable_client import AirtableClient
from src.compress import compress_single_applicant
from src.shortlist import shortlist_applicant
from src.llm_eval import evaluate_applicant
from src.config import TABLE_APPLICANTS

app = Flask(__name__)
client = AirtableClient()


def process_application(record_id: str):
    """Process a single application through the full pipeline"""
    try:
        print(f"Processing application: {record_id}")
        
        # Step 1: Compress
        records = client.get_records(TABLE_APPLICANTS)
        app_record = next((r for r in records if r['id'] == record_id), None)
        
        if not app_record:
            print(f"Record {record_id} not found")
            return
        
        # Compress the applicant data
        compress_single_applicant(client, app_record)
        print(f"✓ Compressed {record_id}")
        
        # Refresh record after compression
        records = client.get_records(TABLE_APPLICANTS)
        app_record = next((r for r in records if r['id'] == record_id), None)
        
        # Step 2: Shortlist
        shortlist_applicant(client, app_record)
        print(f"✓ Shortlisted {record_id}")
        
        # Refresh record after shortlisting
        records = client.get_records(TABLE_APPLICANTS)
        app_record = next((r for r in records if r['id'] == record_id), None)
        
        # Step 3: LLM Evaluation (only if shortlisted)
        if app_record['fields'].get('Shortlist Status') == 'Shortlisted':
            evaluate_applicant(client, app_record)
            print(f"✓ LLM evaluated {record_id}")
        
        print(f"✅ Pipeline complete for {record_id}")
        
    except Exception as e:
        print(f"❌ Error processing {record_id}: {e}")


@app.route('/webhook/new-application', methods=['POST'])
def handle_new_application():
    """
    Webhook endpoint for new applications
    Airtable sends: record ID when a new application is created
    """
    try:
        data = request.json or {}
        record_id = data.get('record_id') or data.get('recordId')
        
        if not record_id:
            return jsonify({'error': 'No record_id provided'}), 400
        
        # Process in background thread so webhook returns quickly
        thread = threading.Thread(target=process_application, args=(record_id,))
        thread.start()
        
        return jsonify({
            'status': 'processing',
            'record_id': record_id,
            'message': 'Pipeline started in background'
        }), 202
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/webhook/compress', methods=['POST'])
def handle_compress():
    """Webhook to trigger compression only"""
    try:
        data = request.json or {}
        record_id = data.get('record_id') or data.get('recordId')
        
        if not record_id:
            return jsonify({'error': 'No record_id provided'}), 400
        
        records = client.get_records(TABLE_APPLICANTS)
        app_record = next((r for r in records if r['id'] == record_id), None)
        
        if not app_record:
            return jsonify({'error': 'Record not found'}), 404
        
        compress_single_applicant(client, app_record)
        
        return jsonify({'status': 'compressed', 'record_id': record_id}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/webhook/shortlist', methods=['POST'])
def handle_shortlist():
    """Webhook to trigger shortlisting only"""
    try:
        data = request.json or {}
        record_id = data.get('record_id') or data.get('recordId')
        
        if not record_id:
            return jsonify({'error': 'No record_id provided'}), 400
        
        records = client.get_records(TABLE_APPLICANTS)
        app_record = next((r for r in records if r['id'] == record_id), None)
        
        if not app_record:
            return jsonify({'error': 'Record not found'}), 404
        
        shortlist_applicant(client, app_record)
        
        return jsonify({'status': 'shortlisted', 'record_id': record_id}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/webhook/llm-eval', methods=['POST'])
def handle_llm_eval():
    """Webhook to trigger LLM evaluation only"""
    try:
        data = request.json or {}
        record_id = data.get('record_id') or data.get('recordId')
        
        if not record_id:
            return jsonify({'error': 'No record_id provided'}), 400
        
        records = client.get_records(TABLE_APPLICANTS)
        app_record = next((r for r in records if r['id'] == record_id), None)
        
        if not app_record:
            return jsonify({'error': 'Record not found'}), 404
        
        evaluate_applicant(client, app_record)
        
        return jsonify({'status': 'evaluated', 'record_id': record_id}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'mercor-pipeline'}), 200


@app.route('/', methods=['GET'])
def home():
    """Home page with API documentation"""
    return jsonify({
        'service': 'Mercor Application Pipeline',
        'endpoints': {
            'POST /webhook/new-application': 'Full pipeline (compress → shortlist → LLM)',
            'POST /webhook/compress': 'Compress only',
            'POST /webhook/shortlist': 'Shortlist only',
            'POST /webhook/llm-eval': 'LLM evaluation only',
            'GET /health': 'Health check'
        },
        'payload': {'record_id': 'airtable_record_id'}
    }), 200


if __name__ == '__main__':
    print("🚀 Starting Mercor Pipeline Webhook Server...")
    print("Endpoints:")
    print("  POST /webhook/new-application - Full pipeline")
    print("  POST /webhook/compress - Compress only")
    print("  POST /webhook/shortlist - Shortlist only")
    print("  POST /webhook/llm-eval - LLM eval only")
    print("  GET  /health - Health check")
    print("")
    app.run(host='0.0.0.0', port=8080, debug=True)
