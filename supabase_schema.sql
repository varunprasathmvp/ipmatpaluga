-- Run this entire script in Supabase SQL Editor.
create table if not exists public.mock_tests (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  exam text not null,
  test_name text not null,
  test_date date not null,
  qa_score numeric not null default 0,
  qa_max numeric not null default 0,
  va_score numeric not null default 0,
  va_max numeric not null default 0,
  lr_score numeric not null default 0,
  lr_max numeric not null default 0,
  total_score numeric not null default 0,
  attempted integer not null default 0,
  correct integer not null default 0,
  created_at timestamptz not null default now()
);

create table if not exists public.question_results (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  exam text not null,
  mock_name text not null,
  question_no text not null,
  section text not null,
  topic text not null,
  result text not null check (result in ('Correct','Incorrect','Unattempted')),
  is_correct boolean not null default false,
  time_seconds integer not null default 0,
  difficulty text not null default 'Unknown',
  created_at timestamptz not null default now()
);

alter table public.mock_tests enable row level security;
alter table public.question_results enable row level security;

create policy "Students manage only their mock tests"
on public.mock_tests for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "Students manage only their question results"
on public.question_results for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);
