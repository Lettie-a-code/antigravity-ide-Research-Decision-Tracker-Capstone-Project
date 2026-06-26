import urllib.parse
import xml.etree.ElementTree as ET
import requests

def reconstruct_openalex_abstract(inverted_index):
    if not inverted_index:
        return ""
    try:
        words = {}
        for word, positions in inverted_index.items():
            for pos in positions:
                words[pos] = word
        return " ".join([words[i] for i in sorted(words.keys())])
    except Exception:
        return ""

def search_openalex(query, limit=10):
    """
    Search OpenAlex API for scholarly works.
    """
    url = f"https://api.openalex.org/works?search={urllib.parse.quote(query)}&per_page={limit}"
    try:
        headers = {"User-Agent": "mailto:student_research_tracker@example.com"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = []
            for work in data.get("results", []):
                # Authors parsing
                authors_list = [author.get("author", {}).get("display_name", "") for author in work.get("authorships", [])]
                authors_str = ", ".join(filter(None, authors_list[:5]))
                if len(authors_list) > 5:
                    authors_str += " et al."
                
                # Venue/Journal
                venue = work.get("primary_location", {}).get("source", {}).get("display_name")
                if not venue:
                    venue = "Unknown Source"
                
                # DOI & URL
                doi = work.get("doi")
                if doi:
                    doi_clean = doi.replace("https://doi.org/", "")
                    url_res = doi
                else:
                    doi_clean = None
                    url_res = work.get("primary_location", {}).get("landing_page_url") or work.get("id")

                # Abstract
                abstract_index = work.get("abstract_inverted_index")
                abstract = reconstruct_openalex_abstract(abstract_index)

                results.append({
                    "title": work.get("title") or "Untitled Paper",
                    "authors": authors_str or "Unknown Authors",
                    "journal": venue,
                    "year": work.get("publication_year"),
                    "url": url_res,
                    "doi": doi_clean,
                    "abstract": abstract or "No abstract available.",
                    "source": "OpenAlex"
                })
            return results
    except Exception as e:
        print(f"OpenAlex search error: {e}")
    return []

def search_arxiv(query, limit=10):
    """
    Search arXiv API using XML feeds.
    """
    url = f"http://export.arxiv.org/api/query?search_query={urllib.parse.quote(query)}&max_results={limit}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            # Register namespaces
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'opensearch': 'http://a9.com/-/spec/opensearch/1.1/',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            results = []
            for entry in root.findall('atom:entry', ns):
                title_node = entry.find('atom:title', ns)
                title = title_node.text.strip().replace('\n', ' ') if title_node is not None else "Untitled Paper"
                
                # Authors
                authors = []
                for author_node in entry.findall('atom:author', ns):
                    name_node = author_node.find('atom:name', ns)
                    if name_node is not None:
                        authors.append(name_node.text.strip())
                authors_str = ", ".join(authors)
                
                # Abstract
                summary_node = entry.find('atom:summary', ns)
                abstract = summary_node.text.strip().replace('\n', ' ') if summary_node is not None else "No abstract available."
                
                # URL and DOI
                url_node = entry.find("atom:id", ns)
                paper_url = url_node.text.strip() if url_node is not None else ""
                
                doi = None
                doi_node = entry.find('arxiv:doi', ns)
                if doi_node is not None:
                    doi = doi_node.text.strip()
                
                # Year from published date
                published_node = entry.find('atom:published', ns)
                year = None
                if published_node is not None:
                    try:
                        year = int(published_node.text[:4])
                    except ValueError:
                        pass
                
                results.append({
                    "title": title,
                    "authors": authors_str or "Unknown Authors",
                    "journal": "arXiv Preprint",
                    "year": year,
                    "url": paper_url,
                    "doi": doi,
                    "abstract": abstract,
                    "source": "arXiv"
                })
            return results
    except Exception as e:
        print(f"arXiv search error: {e}")
    return []

def resolve_doi_openalex(doi):
    """
    Fetch paper metadata directly for a DOI via OpenAlex.
    """
    clean_doi = doi.strip()
    if clean_doi.startswith("http"):
        clean_doi = clean_doi.split("doi.org/")[-1]
        
    url = f"https://api.openalex.org/works/https://doi.org/{clean_doi}"
    try:
        headers = {"User-Agent": "mailto:student_research_tracker@example.com"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            work = response.json()
            authors_list = [author.get("author", {}).get("display_name", "") for author in work.get("authorships", [])]
            authors_str = ", ".join(filter(None, authors_list[:5]))
            if len(authors_list) > 5:
                authors_str += " et al."
            
            venue = work.get("primary_location", {}).get("source", {}).get("display_name") or "Unknown Source"
            abstract_index = work.get("abstract_inverted_index")
            abstract = reconstruct_openalex_abstract(abstract_index)
            
            return {
                "title": work.get("title") or "Untitled Paper",
                "authors": authors_str or "Unknown Authors",
                "journal": venue,
                "year": work.get("publication_year"),
                "url": work.get("doi") or work.get("primary_location", {}).get("landing_page_url") or "",
                "doi": clean_doi,
                "abstract": abstract or "No abstract available.",
                "source": "OpenAlex"
            }
    except Exception as e:
        print(f"DOI resolution error: {e}")
    return None
