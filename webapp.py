from flask import Flask, render_template, request, jsonify
from github_repo_finder import GitHubRepoFinder
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search_repositories():
    try:
        data = request.get_json()
        
        finder = GitHubRepoFinder()
        results = finder.search_repos(
            query=data.get('query', ''),
            language=data.get('language'),
            topics=data.get('topics', []) if data.get('topics') else None,
            stars=int(data.get('stars', 0)) if data.get('stars') else None,
            forks=int(data.get('forks', 0)) if data.get('forks') else None,
            max_results=int(data.get('max_results', 20))
        )
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/analyze', methods=['POST'])
def analyze_repository():
    try:
        data = request.get_json()
        repo_url = data.get('repo_url')
        
        if not repo_url:
            return jsonify({'success': False, 'error': 'Repository URL is required'}), 400
        
        finder = GitHubRepoFinder()
        result = finder.analyze_repo(repo_url)
        
        return jsonify({
            'success': True,
            'analysis': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/search-java-version', methods=['POST'])
def search_java_version():
    try:
        data = request.get_json()
        java_version = data.get('java_version', '8')
        build_tool = data.get('build_tool', '')
        stars = int(data.get('stars', 0)) if data.get('stars') else None
        max_results = int(data.get('max_results', 20))
        
        finder = GitHubRepoFinder()
        results = finder.search_java_version_repos(
            java_version=java_version,
            build_tool=build_tool,
            stars=stars,
            max_results=max_results
        )
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
