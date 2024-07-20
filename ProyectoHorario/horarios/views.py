import pandas as pd
from django.shortcuts import redirect, render
from .forms import UploadFileForm
from datetime import datetime
from itertools import combinations

from datetime import datetime

def parse_horario(horario_str):
    try:
        print(f"Parsing horario: {horario_str}")  # Depuración

        dias_validos = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa', 'Do']
        if not any(horario_str.startswith(dia) for dia in dias_validos):
            print(f"Horario omitido (sin sigla de día): {horario_str}")  # Depuración
            return None, None, None

        partes = horario_str.split(" - ")
        if len(partes) != 2:
            print(f"Error en la división del horario: {partes}")  # Depuración
            return None, None, None

        inicio_str = partes[0].strip()
        fin_str = partes[1].strip()

        if inicio_str == '00:00:00' or fin_str == '00:00:00':
            print(f"Horario omitido: {horario_str}")  # Depuración
            return None, None, None

        horario_parts = inicio_str.split()
        if len(horario_parts) != 2:
            print(f"Error en la división del horario: {horario_parts}")  # Depuración
            return None, None, None

        dia = horario_parts[0].strip()
        inicio_str = horario_parts[1].strip()

        try:
            inicio = datetime.strptime(inicio_str, '%H:%M:%S').time()
            fin = datetime.strptime(fin_str, '%H:%M:%S').time()

            if inicio >= fin:
                print(f"Horario inválido (fin antes de inicio): {horario_str}")  # Depuración
                return None, None, None
        except ValueError as e:
            print(f"Error en la conversión de tiempos: {e}")  # Depuración
            return None, None, None

        dia_map = {
            'Lu': 'Lunes', 'Ma': 'Martes', 'Mi': 'Miércoles', 
            'Ju': 'Jueves', 'Vi': 'Viernes', 'Sa': 'Sábado', 'Do': 'Domingo'
        }
        dia = dia_map.get(dia, dia)

        return dia, inicio, fin
    except Exception as e:
        print(f"Error parsing horario: {e}")  # Depuración
        return None, None, None



def hay_solapamiento(horario1, horario2):
    dia1, inicio1, fin1 = horario1
    dia2, inicio2, fin2 = horario2
    if dia1 != dia2:
        return False
    return not (fin1 <= inicio2 or fin2 <= inicio1)

def generar_horarios_validos(df):
    combinaciones_validas = []
    asignaturas = df['Asignatura'].unique()
    for comb in combinations(asignaturas, len(asignaturas)):
        sub_df = df[df['Asignatura'].isin(comb)]
        sub_df = sub_df.dropna(subset=['Día', 'Hora Inicio', 'Hora Fin'])
        horarios = sub_df[['Asignatura', 'Sección', 'Día', 'Hora Inicio', 'Hora Fin']].values.tolist()
        asignaturas_vistas = set()
        valido = True
        for i in range(len(horarios)):
            asignatura = horarios[i][0]
            if asignatura in asignaturas_vistas:
                valido = False
                break
            asignaturas_vistas.add(asignatura)
            for j in range(i + 1, len(horarios)):
                if hay_solapamiento(horarios[i][2:], horarios[j][2:]):
                    valido = False
                    break
            if not valido:
                break
        if valido:
            combinaciones_validas.append(horarios)
    return combinaciones_validas

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            carrera = form.cleaned_data['carrera']
            df = pd.read_excel(file)
            
            print("DataFrame Original:\n", df.head())

            df = df[df['Carrera'].str.contains(carrera, case=False, na=False)]
            
            print(f"Filas después de filtrar por carrera '{carrera}':\n", df.head())

            df[['Día', 'Hora Inicio', 'Hora Fin']] = df['Horario'].apply(lambda x: pd.Series(parse_horario(x)))
            df = df.dropna(subset=['Día', 'Hora Inicio', 'Hora Fin'])

            df['Hora Inicio'] = df['Hora Inicio'].apply(lambda x: x.strftime('%H:%M:%S'))
            df['Hora Fin'] = df['Hora Fin'].apply(lambda x: x.strftime('%H:%M:%S'))
            
            print("DataFrame después de parsear horarios:\n", df.head())

            request.session['filtered_horarios'] = df.to_dict('records')

            return redirect('ver_horarios')
    else:
        form = UploadFileForm()
    return render(request, 'horarios/upload.html', {'form': form})

def ver_horarios(request):
    filtered_horarios = request.session.get('filtered_horarios', [])
    df = pd.DataFrame(filtered_horarios)
    
    if df.empty:
        print("No se encontraron horarios válidos")  # Depuración
        return render(request, 'horarios/result.html', {'horario': "No se encontraron horarios válidos para la carrera especificada."})
    
    return render(request, 'horarios/ver_horarios.html', {'horarios': df.to_html()})
