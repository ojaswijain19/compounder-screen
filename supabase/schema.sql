-- Run once in Supabase: SQL Editor → New query → paste → Run.
create table if not exists public.user_data (
  user_id uuid primary key references auth.users(id) on delete cascade,
  data jsonb not null default '{}'::jsonb,
  telegram_chat_id text,
  email_alerts boolean not null default false,
  updated_at timestamptz not null default now()
);
alter table public.user_data enable row level security;
drop policy if exists "Users manage their own row" on public.user_data;
create policy "Users manage their own row" on public.user_data
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
