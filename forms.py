from django import forms
from .models import Instrumento, Fornecedor, Cliente, Movimentacao, Manutencao
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario

class UsuarioForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ('username','first_name','last_name','email','funcao')

class InstrumentoForm(forms.ModelForm):
    class Meta:
        model = Instrumento
        fields = ['nome','categoria','preco','quantidade','fornecedor']

class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ['nome','contato','endereco']

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome','contato','observacoes']

class MovimentacaoForm(forms.ModelForm):
    class Meta:
        model = Movimentacao
        fields = ['tipo','data','quantidade','instrumento','cliente','nota']
        widgets = {
            'data': forms.DateTimeInput(attrs={'type':'datetime-local'}),
        }

class ManutencaoForm(forms.ModelForm):
    class Meta:
        model = Manutencao
        fields = ['instrumento','descricao','tecnico_responsavel','prazo','status','cliente','valor_servico']
        widgets = {
            'prazo': forms.DateInput(attrs={'type':'date'}),
        }
