from django.contrib import admin
from .models import Usuario, Fornecedor, Instrumento, Cliente, Movimentacao, Manutencao
from django.contrib.auth.admin import UserAdmin

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Informações da Loja', {'fields': ('funcao',)}),
    )

@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ('nome','contato')

@admin.register(Instrumento)
class InstrumentoAdmin(admin.ModelAdmin):
    list_display = ('nome','categoria','preco','quantidade','fornecedor')
    list_filter = ('categoria','fornecedor')

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome','contato')

@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = ('tipo','instrumento','quantidade','data','usuario','cliente')
    list_filter = ('tipo','data','instrumento')

@admin.register(Manutencao)
class ManutencaoAdmin(admin.ModelAdmin):
    list_display = ('instrumento','status','prazo','tecnico_responsavel')
    list_filter = ('status','prazo')
