import os
from github import Github
from dotenv import load_dotenv
from typing import List, Dict, Optional
import argparse
from tqdm import tqdm
from tabulate import tabulate

class GitHubRepoFinder:
    def __init__(self):
        load_dotenv()
        self.token = os.getenv('GITHUB_TOKEN')
        self.g = Github(self.token)

    def search_repos(self, query: str, language: Optional[str] = None, 
                    topics: Optional[List[str]] = None, 
                    stars: Optional[int] = None, 
                    forks: Optional[int] = None,
                    max_results: int = 100) -> List[Dict]:
        """
        Search GitHub repositories based on various criteria
        
        Args:
            query: Search query string
            language: Programming language filter
            topics: List of topics to filter by
            stars: Minimum number of stars
            forks: Minimum number of forks
            max_results: Maximum number of results to return
            
        Returns:
            List of repository dictionaries containing relevant information
        """
        search_query = query
        print(f"🔧 DEBUG: Building search query...")
        print(f"  Base query: '{query}'")
        
        # Add language filter if specified
        if language:
            search_query += f" language:{language}"
            print(f"  + Language filter: language:{language}")
        
        # Add stars filter if specified
        if stars:
            search_query += f" stars:>{stars}"
            print(f"  + Stars filter: stars:>{stars}")
        
        # Add forks filter if specified
        if forks:
            search_query += f" forks:>{forks}"
            print(f"  + Forks filter: forks:>{forks}")
        
        # Add topics filter if specified
        if topics:
            for topic in topics:
                search_query += f" topic:{topic}"
                print(f"  + Topic filter: topic:{topic}")
        
        # Search repositories
        repos = []
        print(f"🔍 DEBUG: Full GitHub search query: '{search_query}'")
        try:
            search_results = self.g.search_repositories(query=search_query)
            print(f"📊 DEBUG: Total repositories found: {search_results.totalCount}")
            
            for repo in tqdm(search_results, total=min(max_results, 1000)):
                if len(repos) >= max_results:
                    break
                    
                # Calculate repo age
                from datetime import datetime
                repo_age_days = (datetime.now() - repo.created_at.replace(tzinfo=None)).days
                repo_age_years = round(repo_age_days / 365.25, 1)
                
                # Get additional statistics
                try:
                    contributors_count = repo.get_contributors().totalCount
                except:
                    contributors_count = 0
                
                try:
                    commits_count = repo.get_commits().totalCount
                except:
                    commits_count = 0
                
                # Get license info safely
                try:
                    license_name = repo.license.name if repo.license else 'No license'
                except:
                    license_name = 'No license'
                
                # Get last commit info from default branch
                try:
                    default_branch = repo.default_branch
                    commits = repo.get_commits(sha=default_branch)
                    last_commit = commits[0]
                    last_commit_date = last_commit.commit.author.date.strftime('%Y-%m-%d %H:%M')
                    last_commit_author = last_commit.commit.author.name
                    last_commit_message = last_commit.commit.message.split('\n')[0][:100]  # First line, max 100 chars
                except Exception as e:
                    last_commit_date = 'Unknown'
                    last_commit_author = 'Unknown'
                    last_commit_message = 'Unable to fetch commit info'
                
                repo_info = {
                    'name': repo.full_name,
                    'description': repo.description or 'No description',
                    'stars': repo.stargazers_count,
                    'forks': repo.forks_count,
                    'language': repo.language or 'Unknown',
                    'topics': ', '.join(repo.get_topics()) if repo.get_topics() else 'None',
                    'url': repo.html_url,
                    'created_at': repo.created_at.strftime('%Y-%m-%d'),
                    'age_years': repo_age_years,
                    'contributors': contributors_count,
                    'commits': commits_count,
                    'last_updated': repo.updated_at.strftime('%Y-%m-%d'),
                    'size_kb': repo.size,
                    'open_issues': repo.open_issues_count,
                    'license': license_name,
                    'last_commit_date': last_commit_date,
                    'last_commit_author': last_commit_author,
                    'last_commit_message': last_commit_message,
                    'default_branch': repo.default_branch
                }
                repos.append(repo_info)
                
        except Exception as e:
            print(f"Error searching repositories: {str(e)}")
            
        print(f"✅ DEBUG: Search completed. Found {len(repos)} unique repositories")
        return repos

    def search_java_version_repos(self, java_version: str = '8', build_tool: str = '', stars: int = None, max_results: int = 50) -> List[Dict]:
        """
        Search for repositories using a specific Java version with enhanced detection
        
        Args:
            java_version: Java version to search for (8, 11, 17, 21)
            build_tool: Optional build tool filter (maven, gradle, ant)
            stars: Minimum number of stars
            max_results: Maximum number of results
        """
        # Create version-specific search queries
        version_queries = []
        
        # GitHub limits to 5 OR operators per query, so we'll use multiple simpler queries
        base_query = f'language:Java'
        if stars:
            base_query += f' stars:>{stars}'
        if build_tool:
            if build_tool == 'maven':
                base_query += ' pom.xml'
            elif build_tool == 'gradle':
                base_query += ' build.gradle'
            elif build_tool == 'ant':
                base_query += ' build.xml'
        
        # Create multiple queries with max 5 OR operators each
        if java_version == '8':
            version_queries = [
                base_query + ' (java 8 OR java8 OR jdk8 OR "1.8")',
                base_query + ' (lambda OR stream)',
                base_query + ' maven.compiler.source',
                base_query + ' sourceCompatibility'
            ]
        elif java_version == '11':
            version_queries = [
                base_query + ' (java 11 OR java11 OR jdk11)',
                base_query + ' maven.compiler.source 11',
                base_query + ' sourceCompatibility 11'
            ]
        elif java_version == '17':
            version_queries = [
                base_query + ' (java 17 OR java17 OR jdk17)',
                base_query + ' maven.compiler.source 17',
                base_query + ' sourceCompatibility 17'
            ]
        elif java_version == '21':
            version_queries = [
                base_query + ' (java 21 OR java21 OR jdk21)',
                base_query + ' maven.compiler.source 21',
                base_query + ' sourceCompatibility 21'
            ]
        
        print(f"🎯 DEBUG: Using multiple queries approach (GitHub OR limit workaround)")
        
        all_repos = []
        seen_repos = set()
        
        print(f"🔍 DEBUG: Java {java_version} search with {len(version_queries)} queries:")
        for i, query in enumerate(version_queries, 1):
            print(f"  Query {i}: '{query}'")
            try:
                search_results = self.g.search_repositories(query=query)
                print(f"  📊 Results: {search_results.totalCount} repositories found")
                
                for repo in search_results:
                    if len(all_repos) >= max_results:
                        print(f"  ⚙️ DEBUG: Reached max_results ({max_results}), stopping search")
                        break
                    
                    if repo.full_name not in seen_repos:
                        seen_repos.add(repo.full_name)
                        
                        # Calculate repo age
                        from datetime import datetime
                        repo_age_days = (datetime.now() - repo.created_at.replace(tzinfo=None)).days
                        repo_age_years = round(repo_age_days / 365.25, 1)
                        
                        # Get additional statistics with error handling
                        try:
                            contributors_count = repo.get_contributors().totalCount
                        except:
                            contributors_count = 0
                        
                        try:
                            commits_count = repo.get_commits().totalCount
                        except:
                            commits_count = 0
                        
                        try:
                            license_name = repo.license.name if repo.license else 'No license'
                        except:
                            license_name = 'No license'
                        
                        # Get last commit info from default branch
                        try:
                            default_branch = repo.default_branch
                            commits = repo.get_commits(sha=default_branch)
                            last_commit = commits[0]
                            last_commit_date = last_commit.commit.author.date.strftime('%Y-%m-%d %H:%M')
                            last_commit_author = last_commit.commit.author.name
                            last_commit_message = last_commit.commit.message.split('\n')[0][:100]  # First line, max 100 chars
                        except Exception as e:
                            last_commit_date = 'Unknown'
                            last_commit_author = 'Unknown'
                            last_commit_message = 'Unable to fetch commit info'
                        
                        # Calculate Java version confidence score
                        version_score = self._calculate_version_score(repo, java_version)
                        
                        repo_info = {
                            'name': repo.full_name,
                            'description': repo.description or 'No description',
                            'stars': repo.stargazers_count,
                            'forks': repo.forks_count,
                            'language': repo.language or 'Unknown',
                            'topics': ', '.join(repo.get_topics()) if repo.get_topics() else 'None',
                            'url': repo.html_url,
                            'created_at': repo.created_at.strftime('%Y-%m-%d'),
                            'age_years': repo_age_years,
                            'contributors': contributors_count,
                            'commits': commits_count,
                            'last_updated': repo.updated_at.strftime('%Y-%m-%d'),
                            'size_kb': repo.size,
                            'open_issues': repo.open_issues_count,
                            'license': license_name,
                            'java_version': java_version,
                            'version_score': version_score,
                            'last_commit_date': last_commit_date,
                            'last_commit_author': last_commit_author,
                            'last_commit_message': last_commit_message,
                            'default_branch': repo.default_branch
                        }
                        all_repos.append(repo_info)
            except Exception as e:
                print(f"Error in query '{query}': {str(e)}")
                continue
        
        # Sort by version score and stars
        all_repos.sort(key=lambda x: (x['version_score'], x['stars']), reverse=True)
        final_results = all_repos[:max_results]
        print(f"✅ DEBUG: Java {java_version} search completed. Found {len(all_repos)} total repos, returning top {len(final_results)}")
        return final_results
    
    def _calculate_version_score(self, repo, target_version: str) -> int:
        """Calculate confidence score for Java version detection"""
        score = 0
        
        # Check description
        description = (repo.description or '').lower()
        version_keywords = [f'java {target_version}', f'java{target_version}', f'jdk{target_version}']
        
        if target_version == '8':
            version_keywords.extend(['1.8', 'lambda', 'stream'])
        
        for keyword in version_keywords:
            if keyword in description:
                score += 3
        
        # Check topics
        topics = [topic.lower() for topic in repo.get_topics()]
        version_topics = [f'java{target_version}', f'java-{target_version}', f'jdk{target_version}']
        
        for topic in version_topics:
            if topic in topics:
                score += 5
        
        return score

    def analyze_repo(self, repo_url: str) -> Dict:
        """
        Analyze a specific repository for specific characteristics
        
        Args:
            repo_url: URL of the repository to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Extract owner and repo name from URL
            parts = repo_url.strip('/').split('/')
            owner, repo_name = parts[-2], parts[-1]
            
            # Get repository object
            repo = self.g.get_repo(f"{owner}/{repo_name}")
            
            # Check for build tools
            build_tools = []
            if self._check_file_exists(repo, 'pom.xml'):
                build_tools.append('maven')
            if self._check_file_exists(repo, 'build.xml'):
                build_tools.append('ant')
            
            # Check for frameworks
            frameworks = []
            if self._check_file_exists(repo, 'package.json'):
                package_json = self._get_file_content(repo, 'package.json')
                if package_json and 'dependencies' in package_json:
                    if '@angular/core' in package_json['dependencies']:
                        frameworks.append('angular')
            
            return {
                'name': repo.full_name,
                'url': repo.html_url,
                'build_tools': build_tools,
                'frameworks': frameworks,
                'language': repo.language,
                'topics': repo.get_topics()
            }
            
        except Exception as e:
            print(f"Error analyzing repository: {str(e)}")
            return {}

    def _check_file_exists(self, repo, filename: str) -> bool:
        """Check if a file exists in the repository"""
        try:
            repo.get_contents(filename)
            return True
        except:
            return False

    def _get_file_content(self, repo, filename: str) -> Optional[Dict]:
        """Get content of a file as JSON if possible"""
        try:
            content = repo.get_contents(filename)
            return content.decoded_content.decode()
        except:
            return None

def main():
    parser = argparse.ArgumentParser(description='GitHub Repository Finder')
    parser.add_argument('--query', type=str, help='Search query')
    parser.add_argument('--language', type=str, help='Programming language filter')
    parser.add_argument('--topics', nargs='+', help='List of topics to filter by')
    parser.add_argument('--stars', type=int, help='Minimum number of stars')
    parser.add_argument('--forks', type=int, help='Minimum number of forks')
    parser.add_argument('--analyze', type=str, help='Analyze a specific repository URL')
    
    args = parser.parse_args()
    
    finder = GitHubRepoFinder()
    
    if args.analyze:
        result = finder.analyze_repo(args.analyze)
        print("\nAnalysis Results:")
        for key, value in result.items():
            print(f"{key}: {value}")
    else:
        results = finder.search_repos(
            query=args.query,
            language=args.language,
            topics=args.topics,
            stars=args.stars,
            forks=args.forks
        )
        
        print(f"\nFound {len(results)} repositories:\n")
        
        if results:
            # Create a DataFrame for better display
            df_data = []
            for repo in results:
                df_data.append([
                    repo['name'][:40] + '...' if len(repo['name']) > 40 else repo['name'],
                    repo['stars'],
                    repo['forks'],
                    repo['age_years'],
                    repo['contributors'],
                    repo['commits'],
                    repo['language'],
                    repo['open_issues'],
                    repo['license'][:15] + '...' if len(repo['license']) > 15 else repo['license']
                ])
            
            headers = ['Repository', 'Stars', 'Forks', 'Age(Y)', 'Contributors', 'Commits', 'Language', 'Issues', 'License']
            print(tabulate(df_data, headers=headers, tablefmt='grid'))
            
            # Show detailed info for top 3 repositories
            print("\n" + "="*80)
            print("TOP 3 REPOSITORIES - DETAILED VIEW")
            print("="*80)
            
            for i, repo in enumerate(results[:3], 1):
                print(f"\n{i}. {repo['name']}")
                print(f"   URL: {repo['url']}")
                print(f"   Description: {repo['description'][:100]}{'...' if len(repo['description']) > 100 else ''}")
                print(f"   Created: {repo['created_at']} | Last Updated: {repo['last_updated']}")
                print(f"   Stats: ⭐{repo['stars']} | 🍴{repo['forks']} | 👥{repo['contributors']} | 📝{repo['commits']}")
                print(f"   Last Commit: {repo['last_commit_date']} by {repo['last_commit_author']}")
                print(f"   Commit Message: {repo['last_commit_message']}")
                print(f"   Default Branch: {repo['default_branch']}")
                print(f"   Topics: {repo['topics']}")

if __name__ == "__main__":
    main()
