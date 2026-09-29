# 1. Asegúrate de tener el archivo con el nombre exacto en inglés
echo "streamlit" > requirements.txt
echo "mercadopago" >> requirements.txt

# 2. Guarda los cambios en Git
git add requirements.txt
git commit -m "Fix: add mercadopago to requirements.txt"

# 3. Subí los cambios (probamos push a main y a master)
git push origin main || git push origin master
