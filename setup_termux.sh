#!/data/data/com.termux/files/usr/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Oasis CNST — Nutrition News API Setup for Termux
# Run once: bash setup_termux.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e  # Exit on error

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo ""
echo "================================================"
echo "  Oasis CNST — Nutrition News API"
echo "  Termux Setup Script"
echo "================================================"
echo ""

# ── Step 1: System packages ───────────────────────────────────────────────────
info "Updating packages..."
pkg update -y && pkg upgrade -y

info "Installing system dependencies..."
pkg install -y \
    python \
    python-pip \
    libxml2 \
    libxslt \
    openssl \
    libffi \
    rust \
    clang \
    make \
    git

success "System packages installed"

# ── Step 2: Python virtual environment ───────────────────────────────────────
info "Creating Python virtual environment..."
python -m venv venv
source venv/bin/activate

# Upgrade pip first
pip install --upgrade pip setuptools wheel

success "Virtual environment ready"

# ── Step 3: Python packages ───────────────────────────────────────────────────
info "Installing Python packages (this may take a few minutes on mobile)..."

# Install lxml separately first with Termux-specific flags
pip install lxml --no-binary lxml || {
    warn "lxml from source failed, trying wheel..."
    pip install lxml
}

pip install -r requirements.txt

success "Python packages installed"

# ── Step 4: Environment config ────────────────────────────────────────────────
if [ ! -f .env ]; then
    info "Creating .env file..."
    cp .env.example .env

    # Generate a secret key
    SECRET=$(python -c "import secrets; print(secrets.token_hex(50))")
    sed -i "s|your-secret-key-here-generate-with-python-c-.*|$SECRET|g" .env

    success ".env created with generated secret key"
else
    warn ".env already exists — skipping"
fi

# ── Step 5: Django setup ──────────────────────────────────────────────────────
info "Running Django migrations..."
python manage.py migrate

info "Seeding news sources..."
python manage.py seed_sources

info "Collecting static files..."
python manage.py collectstatic --noinput

success "Django setup complete"

# ── Step 6: Create superuser (optional) ──────────────────────────────────────
echo ""
read -p "Create admin superuser? (y/n): " CREATE_SUPER
if [ "$CREATE_SUPER" = "y" ]; then
    python manage.py createsuperuser
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Start the server:"
echo -e "  ${CYAN}source venv/bin/activate${NC}"
echo -e "  ${CYAN}python manage.py runserver 0.0.0.0:8000${NC}"
echo ""
echo "API will be at: http://localhost:8000/api/v1/"
echo ""
echo "Useful commands:"
echo "  python manage.py crawl_now              # manual crawl"
echo "  python manage.py crawl_now --list       # list sources"
echo "  python manage.py crawl_now --source-id 1"
echo "  python manage.py shell                  # Django shell"
echo ""
