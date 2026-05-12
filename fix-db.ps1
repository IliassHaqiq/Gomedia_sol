Write-Host "🔧 Correction du schéma base de données - Gomedia IA" -ForegroundColor Blue
Write-Host "================================================" -ForegroundColor Blue

# Fix 1 : Ajouter la colonne description_length
Write-Host "`n📋 Ajout de la colonne description_length..." -ForegroundColor Yellow
try {
    python -c @"
from sqlalchemy import create_engine, text
import os
db_url = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/gomedia')
engine = create_engine(db_url)
with engine.connect() as conn:
    conn.execute(text("""
        ALTER TABLE specifications ADD COLUMN IF NOT EXISTS description_length VARCHAR(20) DEFAULT 'medium'
    """))
    conn.commit()
print("✅ Colonne ajoutée avec succès")
"@
    Write-Host "✅ Colonne ajoutée avec succès" -ForegroundColor Green
} catch {
    Write-Host "❌ Erreur : $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`n💡 Exécutez ce SQL manuellement dans PostgreSQL :" -ForegroundColor Cyan
    Write-Host "ALTER TABLE specifications ADD COLUMN IF NOT EXISTS description_length VARCHAR(20) DEFAULT 'medium';" -ForegroundColor White
}

# Fix 2 : Configurer le pool (vérification)
Write-Host "`n⚙️ Vérification configuration pool..." -ForegroundColor Yellow
$envFile = ".\.env"
$content = Get-Content $envFile -Raw

$poolVars = @{
    "DATABASE_POOL_SIZE" = "20"
    "DATABASE_MAX_OVERFLOW" = "10"
    "POOL_TIMEOUT" = "30"
}

$updated = $false
foreach ($var in $poolVars.Keys) {
    if ($content -notlike "*$var*") {
        Add-Content $envFile "$var=$($poolVars[$var])"
        Write-Host "  ✅ $var ajouté" -ForegroundColor Green
        $updated = $true
    } else {
        Write-Host "  ✅ $var déjà présent" -ForegroundColor Gray
    }
}

if ($updated) {
    Write-Host "`n💾 Configuration pool mise à jour" -ForegroundColor Green
}

# Résultat
Write-Host "`n" -ForegroundColor Blue
Write-Host "================================================" -ForegroundColor Blue
Write-Host "✅ RÉPARATION TERMINÉE" -ForegroundColor Green -BackgroundColor Black
Write-Host "================================================" -ForegroundColor Blue
Write-Host ""
Write-Host "📝 Prochaines étapes :" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. ARRÊTER le serveur (Ctrl+C)" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. RELANCER l'API :" -ForegroundColor Yellow
Write-Host "   uvicorn app.main:app --reload --port 8000" -ForegroundColor White
Write-Host ""
Write-Host "3. TESTER que tout fonctionne :" -ForegroundColor Yellow
Write-Host "   - curl http://localhost:8000/health/db" -ForegroundColor White
Write-Host "   - curl http://localhost:8000/documents/" -ForegroundColor White
Write-Host ""
Write-Host "🔍 Si Ollama timeout persiste :" -ForegroundColor Red
Write-Host "   - Vérifier qu'Ollama tourne : curl http://localhost:11434/api/tags" -ForegroundColor White
Write-Host "   - Démarrer Ollama : ollama serve" -ForegroundColor White
Write-Host ""
