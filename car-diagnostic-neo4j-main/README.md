# AutoDiag Pro 🚗🔧

**AutoDiag Pro** is an intelligent car diagnostic platform built with **Django** and **Neo4j**. It bridges the gap between drivers, mechanics, and car manufacturers by using a graph database to model complex relationships between vehicle parts, problems, and solutions.

## ✨ Key Features

- **Interactive Visual Dashboard**: A schematic view of the car with clickable hotspots for real-time diagnosis.
- **Role-Based Access Control**:
  - **Drivers**: Diagnose issues, explore DIY vs Professional solutions, and contact experts.
  - **Mechanics**: Manage client requests, contribute to the knowledge base, and build their expertise profile.
  - **Admin (Brand)**: Access advanced analytics on model reliability, failing parts, and knowledge gaps.
- **Neo4j Graph Backend**: High-performance relationship mapping for intelligent recommendations.
- **Localized in French**: Fully tailored for the Moroccan/French-speaking market.

## 🛠️ Tech Stack

- **Backend**: Python, Django
- **Database**: Neo4j (Graph Database)
- **Frontend**: HTML5, Vanilla CSS (Beige/Orange/Military Green Theme), SVG
- **Auth**: Custom Neo4j-based authentication

## 🚀 Getting Started

### Prerequisites

- Python 3.x
- Neo4j Desktop or Server
- Virtual Environment (`venv`)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd car-diagnostic-neo4j
   ```

2. **Setup environment**:
   Create a `.env` file in the root directory:
   ```env
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   DJANGO_SECRET_KEY=your_secret_key
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Seed the database**:
   ```bash
   python seed_data.py
   ```

5. **Run the server**:
   ```bash
   python manage.py runserver
   ```

## 👩‍🏫 Demo Credentials

- **Driver**: `driver` / `123`
- **Mechanic**: `meca` / `123`
- **Admin**: `admin` / `123`

---
*Projet réalisé dans le cadre d'un prototype de diagnostic intelligent.*
