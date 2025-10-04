from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Instrumento, Movimentacao, Fornecedor, Cliente, Manutencao
from .forms import UsuarioForm, InstrumentoForm, MovimentacaoForm, FornecedorForm, ClienteForm, ManutencaoForm
from django.db.models import Sum, F
from django.shortcuts import render, redirect, get_object_or_404

# Mixin de permissões simples por função
class RoleRequiredMixin(UserPassesTestMixin):
    allowed_roles = []
    def test_func(self):
        user = self.request.user
        return (user.is_authenticated and (user.funcao in self.allowed_roles or user.is_superuser))

# Dashboard
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'loja/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # indicadores simples
        ctx['total_produtos'] = Instrumento.objects.count()
        ctx['total_estoque'] = Instrumento.objects.aggregate(total=Sum('quantidade'))['total'] or 0
        ctx['valor_estoque'] = Instrumento.objects.aggregate(valor=Sum(F('quantidade') * F('preco')))['valor'] or 0
        ctx['manutencoes_pendentes'] = Manutencao.objects.filter(status__in=['pendente', 'em_progresso']).count()

        # top vendidos simplificado (requer model de venda real; se vendas são 'Movimentacao' tipo 'saida')
        top = (Movimentacao.objects.filter(tipo='saida')
                .values('instrumento__id','instrumento__nome')
                .annotate(total_vendido=Sum('quantidade'))
                .order_by('-total_vendido')[:10])
        ctx['top_vendidos'] = list(top)
        return ctx

# CRUD Instrumentos
class InstrumentoListView(LoginRequiredMixin, ListView):
    model = Instrumento
    template_name = 'loja/instrumento_list.html'
    paginate_by = 20

class InstrumentoCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = Instrumento
    form_class = InstrumentoForm
    template_name = 'loja/instrumento_form.html'
    success_url = reverse_lazy('instrumento_list')
    allowed_roles = ['admin','gerente']

class InstrumentoUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = Instrumento
    form_class = InstrumentoForm
    template_name = 'loja/instrumento_form.html'
    success_url = reverse_lazy('instrumento_list')
    allowed_roles = ['admin','gerente']

class InstrumentoDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = Instrumento
    template_name = 'loja/instrumento_confirm_delete.html'
    success_url = reverse_lazy('instrumento_list')
    allowed_roles = ['admin','gerente']

# Movimentações
class MovimentacaoListView(LoginRequiredMixin, ListView):
    model = Movimentacao
    template_name = 'loja/movimentacao_list.html'
    paginate_by = 30
    ordering = ['-data']

class MovimentacaoCreateView(LoginRequiredMixin, CreateView):
    model = Movimentacao
    form_class = MovimentacaoForm
    template_name = 'loja/movimentacao_form.html'
    success_url = reverse_lazy('movimentacao_list')

    def form_valid(self, form):
        # seta usuário que registrou
        form.instance.usuario = self.request.user
        # nota: validate estoque quando tipo='saida'
        if form.instance.tipo == 'saida':
            instrumento = form.instance.instrumento
            if form.instance.quantidade > instrumento.quantidade:
                form.add_error('quantidade', 'Quantidade maior que o estoque disponível.')
                return self.form_invalid(form)
        return super().form_valid(form)

# Manutenções
class ManutencaoListView(LoginRequiredMixin, ListView):
    model = Manutencao
    template_name = 'loja/manutencao_list.html'
    paginate_by = 20
    ordering = ['-created_at']

class ManutencaoCreateView(LoginRequiredMixin, CreateView):
    model = Manutencao
    form_class = ManutencaoForm
    template_name = 'loja/manutencao_form.html'
    success_url = reverse_lazy('manutencao_list')

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        # opcional: criar também uma Movimentacao do tipo 'manutencao'
        mov = None
        response = super().form_valid(form)
        return response

# Helpers genéricos para evitar repetição
def _handle_form(request, form_class, redirect_url, titulo, pk=None):
    instance = get_object_or_404(form_class.Meta.model, pk=pk) if pk else None
    form = form_class(request.POST or None, instance=instance)
    if form.is_valid():
        form.save()
        return redirect(redirect_url)
    return render(request, 'loja/form.html', {'form': form, 'titulo': titulo})

def _handle_delete(request, model_class, redirect_url, pk):
    obj = get_object_or_404(model_class, pk=pk)
    if request.method == "POST":
        obj.delete()
        return redirect(redirect_url)
    return render(request, 'loja/confirm_delete.html', {'obj': obj})