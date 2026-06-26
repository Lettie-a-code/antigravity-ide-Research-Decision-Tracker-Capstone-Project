import database as db
import os

def run_tests():
    print("Initializing Database...")
    db.init_db()
    
    # Create project
    print("Testing Project Creation...")
    project_id = db.create_project("Test Project", "A project for automated verification tests.")
    if project_id is None:
        # Maybe it already exists, let's look for it
        projects = db.get_projects()
        for p in projects:
            if p['name'] == "Test Project":
                project_id = p['id']
                print(f"Project 'Test Project' already exists with ID: {project_id}")
                break
    else:
        print(f"Created project 'Test Project' with ID: {project_id}")
        
    assert project_id is not None, "Failed to create project!"
    
    # Log query
    print("Testing Query Logging...")
    query_id = db.log_query(project_id, "quantum computing and cryptography", "arXiv", "Initial test search")
    print(f"Logged query with ID: {query_id}")
    
    # Add resource
    print("Testing Resource Insertion...")
    resource_id = db.add_resource(
        project_id=project_id,
        title="Post-Quantum Cryptography in Practice",
        authors="Alice Smith, Bob Jones",
        journal="Journal of Security Studies",
        year=2025,
        url="https://example.com/pqc",
        doi="10.1234/testdoi",
        abstract="This paper discusses how quantum computers affect current public key cryptosystems and evaluates transition options.",
        source_query_id=query_id
    )
    print(f"Added resource with ID: {resource_id}")
    
    # Record decision
    print("Testing Decision Recording...")
    success = db.record_decision(resource_id, "Selected", "Important background reference on timeline mapping.")
    assert success, "Failed to record decision!"
    print("Recorded decision successfully.")
    
    # Fetch timeline
    print("Testing Timeline Retrieve...")
    events = db.get_timeline(project_id)
    print(f"Found {len(events)} events in timeline.")
    assert len(events) >= 4, "Timeline does not contain expected events!"
    
    # Get analytics
    print("Testing Analytics...")
    analytics = db.get_analytics(project_id)
    print(f"Analytics results: {analytics}")
    assert analytics['decisions'].get('Selected', 0) >= 1, "Analytics missing recorded decision!"
    
    print("\nAll database tests passed successfully!")

if __name__ == "__main__":
    try:
        run_tests()
        # Clean up database test project to keep it tidy
        projects = db.get_projects()
        for p in projects:
            if p['name'] == "Test Project":
                db.delete_project(p['id'])
                print("Cleaned up Test Project successfully.")
    except Exception as e:
        print(f"Test failed with error: {e}")
