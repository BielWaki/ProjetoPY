# app called "loja"
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.db import transaction


# 1. Usuário estendido com função (role)
class Usuario(AbstractUser):
    # usa username/email do AbstractUser
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('gerente', 'Gerente'),
        ('vendedor', 'Vendedor'),
        ('caixa', 'Caixa'),
    ]
    funcao = models.CharField(max_length=20, choices=ROLE_CHOICES, default='vendedor')

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.funcao})"


# 2. Fornecedores
class Fornecedor(models.Model):
    nome = models.CharField(max_length=200)
    contato = models.CharField(max_length=200, blank=True, null=True, help_text="Email ou telefone do fornecedor.")
    endereco = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome


# 3. Instrumentos (produto)
class Instrumento(models.Model):
    CATEGORY_CHOICES = [
        ('cordas', 'Cordas'),
        ('sopro', 'Sopro'),
        ('percussao', 'Percussão'),
        ('teclados', 'Teclados'),
        ('acessorios', 'Acessórios'),
    ]
    nome = models.CharField(max_length=200)
    categoria = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    preco = models.DecimalField(max_digits=10, decimal_places=2, help_text="Preço de venda.")
    quantidade = models.PositiveIntegerField(default=0, help_text="Quantidade em estoque.")
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.SET_NULL, null=True, blank=True, related_name='instrumentos')
    def __str__(self):
        return f"{self.nome} - {self.categoria}"

    class Meta:
        ordering = ['nome']


# 4. Clientes
class Cliente(models.Model):
    nome = models.CharField(max_length=200)
    contato = models.CharField(max_length=200, blank=True, null=True, help_text="Email ou telefone do cliente.")
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome


# 5. Movimentações (entrada/saida/manutenção) — registro genérico
class Movimentacao(models.Model):
    TYPE_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
        ('manutencao', 'Manutenção'),
    ]
    tipo = models.CharField(max_length=20, choices=TYPE_CHOICES)
    data = models.DateTimeField(default=timezone.now)
    quantidade = models.PositiveIntegerField()
    instrumento = models.ForeignKey(Instrumento, on_delete=models.PROTECT, related_name='movimentacoes')
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, help_text="Usuário que registrou a movimentação.")
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, help_text="Cliente associado (apenas para saídas/vendas).")
    nota = models.CharField(max_length=200, blank=True, null=True, help_text="Observação ou número da nota fiscal.")
    def save(self, *args, **kwargs):
        # Ao salvar, atualiza o estoque automaticamente (atenção: evite duplicação em updates)
        is_create = self._state.adding
        previous = None
        if not is_create:
            # se update, buscar quantidade anterior para ajustar corretamente
            try:
                previous = Movimentacao.objects.get(pk=self.pk)
            except Movimentacao.DoesNotExist:
                previous = None

        super().save(*args, **kwargs)  # salva primeiro (ou poderia atualizar estoque antes)

        # Ajuste simples: só aplica alteração se for criação; para updates, lógica mais cuidadosa
        if is_create:
            if self.tipo == 'entrada':
                self.instrumento.quantidade += self.quantidade
            elif self.tipo == 'saida':
                self.instrumento.quantidade -= self.quantidade
            # manutenção não altera quantidade por padrão (a não ser que faça retirada temporária)
            self.instrumento.save()

    def __str__(self):
        return f"{self.tipo} | {self.instrumento.nome} | {self.quantidade} em {self.data.date()}"


# 6. Manutenções (detalhe extra) — vinculado a Movimentacao (opcional duplicado) ou separado
class Manutencao(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_progresso', 'Em progresso'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
    ]
    movimentacao = models.OneToOneField(Movimentacao, on_delete=models.CASCADE, related_name='manutencao', null=True, blank=True)
    instrumento = models.ForeignKey(Instrumento, on_delete=models.CASCADE)
    descricao = models.TextField()
    tecnico_responsavel = models.CharField(max_length=200, blank=True, null=True)
    prazo = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)  # quem registrou

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    valor_servico = models.DecimalField(max_digits=9, decimal_places=2, default=0)

    def __str__(self):
        return f"Manutenção {self.id} - {self.instrumento.nome} ({self.status})"
