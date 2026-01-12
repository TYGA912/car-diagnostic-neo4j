from django.shortcuts import render, redirect
from .neo4j_driver import Neo4jDriver

def get_db_session():
    driver = Neo4jDriver.get_driver()
    return driver.session()

def login_view(request):
    if request.method == "POST":
        u = request.POST.get("username")
        p = request.POST.get("password")
        
        query = """
        MATCH (u:User {username: $u, password: $p})
        RETURN u.name AS name, labels(u) AS labels, elementId(u) as id
        """
        with get_db_session() as session:
            result = session.run(query, u=u, p=p).single()
            
        if result:
            request.session['user_name'] = result['name']
            request.session['user_id'] = result['id']
            labels = result['labels']
            
            if "Mechanic" in labels:
                request.session['role'] = 'Mechanic'
                return redirect("mechanic_dashboard")
            elif "Admin" in labels:
                request.session['role'] = 'Admin'
                return redirect("admin_dashboard")
            else:
                request.session['role'] = 'Driver'
                # Find the car owned by this driver
                car_query = "MATCH (u:User)-[:OWNS]->(c:Car) WHERE elementId(u) = $uid RETURN c.model AS model"
                with get_db_session() as session:
                    car_res = session.run(car_query, uid=result['id']).single()
                
                model = car_res['model'] if car_res else "Corolla" # Default fallback
                return redirect("dashboard", car_model=model)
        else:
            return render(request, "diagnosis/login.html", {"error": "Invalid credentials"})
            
    return render(request, "diagnosis/login.html")

def logout_view(request):
    request.session.flush()
    return redirect("login")

def admin_dashboard(request):
    # Analytics Queries
    
    # 1. Models with most problems (Zone Rouge)
    query_models = """
    MATCH (c:Car)-[:HAS_PART]->(p:Part)-[:HAS_PROBLEM]->(pr:Problem)
    RETURN c.model as model, count(pr) as problem_count
    ORDER BY problem_count DESC
    """
    
    # 2. Parts prone to failure (Maillons Faibles)
    query_parts = """
    MATCH (p:Part)-[:HAS_PROBLEM]->(pr:Problem)
    RETURN p.name as part, count(pr) as count
    ORDER BY count DESC LIMIT 5
    """
    
    # 3. Content Gaps (Problems without solutions)
    query_gaps = """
    MATCH (pr:Problem)
    WHERE NOT (pr)-[:HAS_SOLUTION]->()
    OPTIONAL MATCH (p:Part)-[:HAS_PROBLEM]->(pr)
    RETURN pr.description as problem, p.name as part, pr.severity as severity
    """
    
    # 4. Global Stats
    query_stats = """
    MATCH (c:Car) WITH count(c) as cars
    MATCH (m:Mechanic) WITH cars, count(m) as mechanics
    MATCH (s:Solution) WITH cars, mechanics, count(s) as solutions
    RETURN cars, mechanics, solutions
    """

    with get_db_session() as session:
        models_data = [record.data() for record in session.run(query_models)]
        parts_data = [record.data() for record in session.run(query_parts)]
        gaps_data = [record.data() for record in session.run(query_gaps)]
        stats = session.run(query_stats).single()

    context = {
        "admin_name": request.session.get('user_name', 'Admin'),
        "models_data": models_data,
        "parts_data": parts_data,
        "gaps_data": gaps_data,
        "stats": stats
    }
    return render(request, "diagnosis/admin_dashboard.html", context)

def mechanic_dashboard(request):
    # Fetch REAL requests from Neo4j
    # Match requests sent TO the logged-in mechanic (User:Mechanic)
    mech_id = request.session.get('user_id')
    query = """
    MATCH (u:User)-[:REQUESTED]->(r:Request)-[:TO]->(m:User:Mechanic)
    WHERE elementId(m) = $mech_id AND r.status = 'PENDING'
    OPTIONAL MATCH (u)-[:OWNS]->(c:Car)
    RETURN r.issue as issue, r.date as date, u.name as client, elementId(r) as id, COALESCE(c.model, 'Non spécifié') as car
    """
    # Note: simplified car logic for demo
    
    with get_db_session() as session:
        # Fetch Pending Requests
        query_pending = """
        MATCH (u:User)-[:REQUESTED]->(r:Request)-[:TO]->(m:User:Mechanic)
        WHERE elementId(m) = $mech_id AND r.status = 'PENDING'
        OPTIONAL MATCH (u)-[:OWNS]->(c:Car)
        RETURN r.issue as issue, r.date as date, u.name as client, elementId(r) as id, COALESCE(c.model, 'Non spécifié') as car
        ORDER BY r.date DESC
        """
        pending_requests = [record.data() for record in session.run(query_pending, mech_id=mech_id)]
        
        # Fetch Request History (Accepted/Refused)
        query_history = """
        MATCH (u:User)-[:REQUESTED]->(r:Request)-[:TO]->(m:User:Mechanic)
        WHERE elementId(m) = $mech_id AND r.status <> 'PENDING'
        OPTIONAL MATCH (u)-[:OWNS]->(c:Car)
        RETURN r.issue as issue, r.date as date, u.name as client, elementId(r) as id, COALESCE(c.model, 'Non spécifié') as car, r.status as status
        ORDER BY r.date DESC
        """
        history_requests = [record.data() for record in session.run(query_history, mech_id=mech_id)]
        
    context = {
        "mechanic_name": request.session.get('user_name', 'Mécano'),
        "pending_requests": pending_requests,
        "history_requests": history_requests
    }
    return render(request, "diagnosis/mechanic_dashboard.html", context)

def handle_request(request, request_id, action):
    # Update Request status in Neo4j
    status = 'ACCEPTED' if action == 'accept' else 'REFUSED'
    
    query = """
    MATCH (r:Request)
    WHERE id(r) = $req_id
    SET r.status = $status
    """
    # Note: id() integer lookup for simplicity in demo, though elementId is better in v5
    # Since we passed integer ID from template, we assume integer id usage or handle conversion.
    # Actually, let's use elementId matching if possible, but template passed int.
    # Let's try matching by id() for simplicity with older Neo4j or elementId string.
    
    # Correction: The dashboard query returned `elementId(r) as id`. So request_id is a string.
    query = """
    MATCH (r:Request)
    WHERE elementId(r) = $req_id
    SET r.status = $status
    """

    with get_db_session() as session:
        session.run(query, req_id=request_id, status=status)
    
    return redirect("mechanic_dashboard")

def mechanic_problem_select(request):
    # List all problems so the mechanic can choose one to add a solution to
    query = """
    MATCH (c:Car)-[:HAS_PART]->(p:Part)-[:HAS_PROBLEM]->(pr:Problem)
    RETURN c.model AS car, p.name AS part, pr.description AS description, pr.severity AS severity
    """
    with get_db_session() as session:
        result = session.run(query)
        problems = [record.data() for record in result]
        
    return render(request, "diagnosis/mechanic_problem_select.html", {"problems": problems})

def mechanic_solutions(request):
    # Fetch all solutions grouped by part to display in the knowledge base
    query = """
    MATCH (p:Part)-[:HAS_PROBLEM]->(pr:Problem)-[:HAS_SOLUTION]->(s:Solution)
    OPTIONAL MATCH (m:Mechanic)-[:POSTED]->(s)
    RETURN p.name as part, pr.description as problem, s.description as solution, s.cost_range as cost, s.type as type, m.name as author
    ORDER BY p.name
    """
    
    with get_db_session() as session:
        result = session.run(query)
        data = [record.data() for record in result]
        
    # Group data by part for the template
    parts_dict = {}
    for item in data:
        p_name = item['part']
        if p_name not in parts_dict:
            parts_dict[p_name] = []
        
        parts_dict[p_name].append({
            "problem": item['problem'],
            "solution": item['solution'],
            "cost": item['cost'],
            "type": item['type'],
            "author": item['author'] if item['author'] else "Système/Inconnu"
        })
    
    parts_data = [{"name": k, "solutions": v} for k, v in parts_dict.items()]
        
    return render(request, "diagnosis/mechanic_solution_list.html", {"parts_data": parts_data})

def dashboard(request, car_model):
    # Retrieve parts for a specific car model with their coordinates for the visual dashboard
    query = """
    MATCH (c:Car {model: $car_model})-[:HAS_PART]->(p:Part)
    RETURN c.brand AS brand, c.model AS model, p.name AS part_name, elementId(p) as id, p.x_pos as x, p.y_pos as y
    """
    with get_db_session() as session:
        result = session.run(query, car_model=car_model)
        parts = [record.data() for record in result]
        
    context = {
        "car_model": car_model,
        "parts": parts,
        "brand": parts[0]['brand'] if parts else ""
    }
    return render(request, "diagnosis/dashboard.html", context)

def part_list(request, car_model):
    # Retrieve parts for a specific car model
    query = """
    MATCH (c:Car {model: $car_model})-[:HAS_PART]->(p:Part)
    RETURN c.brand AS brand, c.model AS model, p.name AS part_name, elementId(p) as id
    """
    with get_db_session() as session:
        result = session.run(query, car_model=car_model)
        parts = [record.data() for record in result]
        
    context = {
        "car_model": car_model,
        "parts": parts,
        "brand": parts[0]['brand'] if parts else ""
    }
    return render(request, "diagnosis/part_list.html", context)

def problem_list(request, car_model, part_name):
    query = """
    MATCH (c:Car {model: $car_model})-[:HAS_PART]->(p:Part {name: $part_name})-[:HAS_PROBLEM]->(pr:Problem)
    RETURN p.name as part_name, pr.description as description, pr.severity as severity, elementId(pr) as id
    """
    with get_db_session() as session:
        result = session.run(query, car_model=car_model, part_name=part_name)
        problems = [record.data() for record in result]

    context = {
        "car_model": car_model,
        "part_name": part_name,
        "problems": problems
    }
    return render(request, "diagnosis/problem_list.html", context)

def solution_list(request, car_model, part_name, problem_description):
    # Fetch DIY Solutions
    query_diy = """
    MATCH (pr:Problem {description: $problem_description})-[:HAS_SOLUTION]->(s:Solution {type: 'DIY'})
    RETURN s.description as solution, s.cost_range as cost, elementId(s) as id
    """
    
    # Fetch Pro Solutions (and who posted them if applicable)
    query_pro = """
    MATCH (pr:Problem {description: $problem_description})-[:HAS_SOLUTION]->(s:Solution {type: 'Professional'})
    OPTIONAL MATCH (m:Mechanic)-[:POSTED]->(s)
    RETURN s.description as solution, s.cost_range as cost, m.name as mechanic_name, elementId(s) as id
    """

    # Fetch Experts for this Part
    query_experts = """
    MATCH (m:Mechanic)-[:EXPERT_IN]->(p:Part {name: $part_name})
    RETURN m.name as name, m.location as location, m.rating as rating
    """

    with get_db_session() as session:
        diy_solutions = [record.data() for record in session.run(query_diy, problem_description=problem_description)]
        pro_solutions = [record.data() for record in session.run(query_pro, problem_description=problem_description)]
        experts = [record.data() for record in session.run(query_experts, part_name=part_name)]

    context = {
        "car_model": car_model,
        "part_name": part_name,
        "problem_description": problem_description,
        "diy_solutions": diy_solutions,
        "pro_solutions": pro_solutions,
        "experts": experts
    }
    return render(request, "diagnosis/solution_list.html", context)

def add_solution(request, problem_description):
    if request.method == "POST":
        description = request.POST.get("description")
        cost = request.POST.get("cost")
        # mechanic_name = request.POST.get("mechanic_name") # Not used, we use logged in user
        
        mech_id = request.session.get('user_id')
        
        query = """
        MATCH (pr:Problem {description: $problem_desc})
        MATCH (m:User:Mechanic) WHERE elementId(m) = $mech_id
        CREATE (s:Solution {description: $desc, cost_range: $cost, type: 'Professional'})
        CREATE (pr)-[:HAS_SOLUTION]->(s)
        CREATE (m)-[:POSTED]->(s)
        """
        
        with get_db_session() as session:
            session.run(query, problem_desc=problem_description, desc=description, cost=cost, mech_id=mech_id)
        
        return redirect('mechanic_solution_list')
    
    return render(request, "diagnosis/add_solution.html", {"problem_description": problem_description})

def contact_mechanic(request, mechanic_name):
    if request.method == "POST":
        client_name = request.POST.get("client_name") # Or use logged in user name
        issue = request.POST.get("message")
        
        # We need to find the user sending this request (Driver) and the Mechanic receiving it
        # We find the mechanic by name since that's what we have in the URL (not ideal but works for demo)
        # Better: Pass mecahnic ID. 
        # For now, matching by name 'Ahmed' (which is now also a User)
        
        driver_id = request.session.get('user_id')
        
        query = """
        MATCH (u:User) WHERE elementId(u) = $driver_id
        MATCH (m:User:Mechanic {name: $mech_name})
        CREATE (r:Request {issue: $issue, date: date(), status: 'PENDING'})
        CREATE (u)-[:REQUESTED]->(r)-[:TO]->(m)
        """
        
        with get_db_session() as session:
            session.run(query, driver_id=driver_id, mech_name=mechanic_name, issue=issue)

        return render(request, "diagnosis/contact_success.html", {"mechanic_name": mechanic_name})
        
    return render(request, "diagnosis/contact_mechanic.html", {"mechanic_name": mechanic_name})

# ------------------------------
# ADMIN MANAGEMENT VIEWS
# ------------------------------

def admin_users_list(request):
    query = """
    MATCH (u:User)
    RETURN elementId(u) as id, u.name as name, u.username as username, labels(u) as labels
    ORDER BY u.name
    """
    with get_db_session() as session:
        users = [record.data() for record in session.run(query)]
    return render(request, "diagnosis/admin_user_list.html", {"users": users})

def admin_user_add(request):
    if request.method == "POST":
        role = request.POST.get("role")
        name = request.POST.get("name")
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        # Optional fields
        location = request.POST.get("location", "")
        rating = request.POST.get("rating", "")
        
        label = "Mechanic" if role == "Mechanic" else "Driver"
        
        if role == "Mechanic":
            query = f"""
            CREATE (u:User:Mechanic {{name: $name, username: $username, password: $password, location: $location, rating: $rating}})
            """
            rating_val = float(rating) if rating else 0.0
            params = {"name": name, "username": username, "password": password, "location": location, "rating": rating_val}
        else:
            query = f"""
            CREATE (u:User:Driver {{name: $name, username: $username, password: $password}})
            """
            params = {"name": name, "username": username, "password": password}

        with get_db_session() as session:
            session.run(query, **params)
            
        return redirect("admin_users_list")
        
    return render(request, "diagnosis/admin_user_form.html", {"user": {}})

def admin_user_edit(request, user_id):
    if request.method == "POST":
        name = request.POST.get("name")
        username = request.POST.get("username")
        password = request.POST.get("password")
        location = request.POST.get("location")
        rating = request.POST.get("rating")
        
        query = """
        MATCH (u:User) WHERE elementId(u) = $uid
        SET u.name = $name, u.username = $username, u.password = $password
        """
        params = {"uid": user_id, "name": name, "username": username, "password": password}
        
        if location is not None:
             query += ", u.location = $location, u.rating = $rating"
             params["location"] = location
             params["rating"] = float(rating) if rating else 0.0
             
        with get_db_session() as session:
            session.run(query, **params)
        return redirect("admin_users_list")

    query = "MATCH (u:User) WHERE elementId(u) = $uid RETURN u.name as name, u.username as username, u.password as password, u.location as location, u.rating as rating, labels(u) as labels, elementId(u) as id"
    with get_db_session() as session:
        user = session.run(query, uid=user_id).single().data()
        
    role = "Mechanic" if "Mechanic" in user['labels'] else "Driver"
    return render(request, "diagnosis/admin_user_form.html", {"user": user, "role": role})

def admin_user_delete(request, user_id):
    if request.method == "POST":
        query = "MATCH (u:User) WHERE elementId(u) = $uid DETACH DELETE u"
        with get_db_session() as session:
            session.run(query, uid=user_id)
    return redirect("admin_users_list")

def admin_problems_list(request):
    query = """
    MATCH (c:Car)
    OPTIONAL MATCH (c)-[:HAS_PART]->(p:Part)
    OPTIONAL MATCH (p)-[:HAS_PROBLEM]->(pr:Problem)
    RETURN c.model as model, p.name as part, collect(properties(pr)) as problems
    ORDER BY c.model, p.name
    """
    
    with get_db_session() as session:
        result = session.run(query)
        data = [record.data() for record in result]
        
    structured_data = {}
    for row in data:
        model = row['model']
        if model not in structured_data:
            structured_data[model] = {}
        
        part = row['part']
        if part:
            if part not in structured_data[model]:
                structured_data[model][part] = []
            
            problems = [p for p in row['problems'] if p]
            structured_data[model][part] = problems
            
    final_list = []
    for model, parts_dict in structured_data.items():
        parts_list = []
        for p_name, probs in parts_dict.items():
            parts_list.append({"name": p_name, "problems": probs})
        final_list.append({"model": model, "parts": parts_list})
        
    return render(request, "diagnosis/admin_problems_list.html", {"data": final_list})
