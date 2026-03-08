--
-- PostgreSQL database dump
--

\restrict Fs19ThtIRBl7Qm64BOeyLZXO7UCREnPjmmDAZmx9vAdeOkqAgygqereVQjdmr7Q

-- Dumped from database version 15.16 (Debian 15.16-1.pgdg13+1)
-- Dumped by pg_dump version 15.16 (Debian 15.16-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: intraday_user
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
   NEW.updated_at = now();
   RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO intraday_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: account; Type: TABLE; Schema: public; Owner: intraday_user
--

CREATE TABLE public.account (
    id integer NOT NULL,
    total_capital double precision DEFAULT 50000 NOT NULL,
    used_capital double precision DEFAULT 0 NOT NULL,
    daily_pnl double precision DEFAULT 0 NOT NULL,
    daily_loss_limit double precision DEFAULT '-1500'::integer NOT NULL,
    intraday_peak_equity numeric,
    current_equity numeric,
    is_trading_enabled boolean DEFAULT true,
    breach_count integer DEFAULT 0,
    last_breach_reason text,
    last_breach_time timestamp without time zone
);


ALTER TABLE public.account OWNER TO intraday_user;

--
-- Name: account_id_seq; Type: SEQUENCE; Schema: public; Owner: intraday_user
--

CREATE SEQUENCE public.account_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.account_id_seq OWNER TO intraday_user;

--
-- Name: account_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: intraday_user
--

ALTER SEQUENCE public.account_id_seq OWNED BY public.account.id;


--
-- Name: equity_history; Type: TABLE; Schema: public; Owner: intraday_user
--

CREATE TABLE public.equity_history (
    id integer NOT NULL,
    account_id integer NOT NULL,
    equity numeric(18,2) NOT NULL,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.equity_history OWNER TO intraday_user;

--
-- Name: equity_history_id_seq; Type: SEQUENCE; Schema: public; Owner: intraday_user
--

CREATE SEQUENCE public.equity_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.equity_history_id_seq OWNER TO intraday_user;

--
-- Name: equity_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: intraday_user
--

ALTER SEQUENCE public.equity_history_id_seq OWNED BY public.equity_history.id;


--
-- Name: event_log; Type: TABLE; Schema: public; Owner: intraday_user
--

CREATE TABLE public.event_log (
    id integer NOT NULL,
    event_id text NOT NULL,
    event_type text NOT NULL,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.event_log OWNER TO intraday_user;

--
-- Name: event_log_id_seq; Type: SEQUENCE; Schema: public; Owner: intraday_user
--

CREATE SEQUENCE public.event_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.event_log_id_seq OWNER TO intraday_user;

--
-- Name: event_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: intraday_user
--

ALTER SEQUENCE public.event_log_id_seq OWNED BY public.event_log.id;


--
-- Name: order_rate_limit; Type: TABLE; Schema: public; Owner: intraday_user
--

CREATE TABLE public.order_rate_limit (
    id integer NOT NULL,
    account_id integer NOT NULL,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.order_rate_limit OWNER TO intraday_user;

--
-- Name: order_rate_limit_id_seq; Type: SEQUENCE; Schema: public; Owner: intraday_user
--

CREATE SEQUENCE public.order_rate_limit_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.order_rate_limit_id_seq OWNER TO intraday_user;

--
-- Name: order_rate_limit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: intraday_user
--

ALTER SEQUENCE public.order_rate_limit_id_seq OWNED BY public.order_rate_limit.id;


--
-- Name: positions; Type: TABLE; Schema: public; Owner: intraday_user
--

CREATE TABLE public.positions (
    id integer NOT NULL,
    symbol character varying(50) NOT NULL,
    quantity integer DEFAULT 0 NOT NULL,
    entry_price double precision DEFAULT 0 NOT NULL,
    account_id integer NOT NULL,
    stop_loss numeric,
    trailing_distance numeric,
    highest_price numeric
);


ALTER TABLE public.positions OWNER TO intraday_user;

--
-- Name: positions_id_seq; Type: SEQUENCE; Schema: public; Owner: intraday_user
--

CREATE SEQUENCE public.positions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.positions_id_seq OWNER TO intraday_user;

--
-- Name: positions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: intraday_user
--

ALTER SEQUENCE public.positions_id_seq OWNED BY public.positions.id;


--
-- Name: risk_config; Type: TABLE; Schema: public; Owner: intraday_user
--

CREATE TABLE public.risk_config (
    id integer NOT NULL,
    max_allocation_pct numeric(5,2) NOT NULL,
    max_exposure_pct numeric(5,2) NOT NULL,
    daily_loss_limit numeric(12,2) NOT NULL,
    max_open_positions integer NOT NULL,
    updated_at timestamp without time zone DEFAULT now(),
    account_id integer NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    max_symbol_exposure_pct numeric(5,2) DEFAULT 25,
    max_portfolio_heat_pct double precision DEFAULT 0.3
);


ALTER TABLE public.risk_config OWNER TO intraday_user;

--
-- Name: risk_config_id_seq; Type: SEQUENCE; Schema: public; Owner: intraday_user
--

CREATE SEQUENCE public.risk_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.risk_config_id_seq OWNER TO intraday_user;

--
-- Name: risk_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: intraday_user
--

ALTER SEQUENCE public.risk_config_id_seq OWNED BY public.risk_config.id;


--
-- Name: trade_audit; Type: TABLE; Schema: public; Owner: intraday_user
--

CREATE TABLE public.trade_audit (
    id integer NOT NULL,
    symbol text NOT NULL,
    quantity integer NOT NULL,
    price numeric NOT NULL,
    side text NOT NULL,
    simulated_equity numeric,
    simulated_drawdown numeric,
    simulated_total_pnl numeric,
    status text NOT NULL,
    rejection_reason text,
    created_at timestamp without time zone DEFAULT now(),
    account_id integer DEFAULT 1 NOT NULL
);


ALTER TABLE public.trade_audit OWNER TO intraday_user;

--
-- Name: trade_audit_id_seq; Type: SEQUENCE; Schema: public; Owner: intraday_user
--

CREATE SEQUENCE public.trade_audit_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.trade_audit_id_seq OWNER TO intraday_user;

--
-- Name: trade_audit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: intraday_user
--

ALTER SEQUENCE public.trade_audit_id_seq OWNED BY public.trade_audit.id;


--
-- Name: trades; Type: TABLE; Schema: public; Owner: intraday_user
--

CREATE TABLE public.trades (
    id integer NOT NULL,
    order_idempotency_key character varying(100) NOT NULL,
    symbol character varying(50) NOT NULL,
    quantity integer NOT NULL,
    entry_price double precision NOT NULL,
    status character varying(50) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    exit_price double precision,
    pnl double precision,
    account_id integer DEFAULT 1 NOT NULL,
    strategy_name text
);


ALTER TABLE public.trades OWNER TO intraday_user;

--
-- Name: trades_id_seq; Type: SEQUENCE; Schema: public; Owner: intraday_user
--

CREATE SEQUENCE public.trades_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.trades_id_seq OWNER TO intraday_user;

--
-- Name: trades_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: intraday_user
--

ALTER SEQUENCE public.trades_id_seq OWNED BY public.trades.id;


--
-- Name: account id; Type: DEFAULT; Schema: public; Owner: intraday_user
--

ALTER TABLE ONLY public.account ALTER COLUMN id SET DEFAULT nextval('public.account_id_seq'::regclass);


--
-- Name: equity_history id; Type: DEFAULT; Schema: public; Owner: intraday_user
--

ALTER TABLE ONLY public.equity_history ALTER COLUMN id SET DEFAULT nextval('public.equity_history_id_seq'::regclass);


--
-- Name: event_log id; Type: DEFAULT; Schema: public; Owner: intraday_user
--

ALTER TABLE ONLY public.event_log ALTER COLUMN id SET DEFAULT nextval('public.event_log_id_seq'::regclass);


--
-- Name: order_rate_limit id; Type: DEFAULT; Schema: public; Owner: intraday_user
--

ALTER TABLE ONLY public.order_rate_limit ALTER COLUMN id SET DEFAULT nextval('public.order_rate_limit_id_seq'::regclass);


--
-- Name: positions id; Type: DEFAULT; Schema: public; Owner: intraday_user
--

ALTER TABLE ONLY public.positions ALTER COLUMN id SET DEFAULT nextval('public.positions_id_seq'::regclass);


--
-- Name: risk_config id; Type: DEFAULT; Schema: public; Owner: intraday_user
--

ALTER TABLE ONLY public.risk_config ALTER COLUMN id SET DEFAULT nextval('public.risk_config_id_seq'::regclass);


--
-- Name: trade_audit id; Type: DEFAULT; Schema: public; Owner: intraday_user
--

ALTER TABLE ONLY public.trade_audit ALTER COLUMN id SET DEFAULT nextval('public.trade_audit_id_seq'::regclass);


--
-- Name: trades id; Type: DEFAULT; Schema: public; Owner: intraday_user
--

ALTER TABLE ONLY public.trades ALTER COLUMN id SET DEFAULT nextval('public.trades_id_seq'::regclass);


--
-- Name: account account_pkey; Type: CONSTRAINT; Schema: public; Owner: intraday_user
--

ALTER TABLE ONLY public.account
    ADD CONSTRAINT account_pkey PRIMARY KEY (id);


--
-- Name: equity_history equity_history_pkey; Type: CONSTRAINT; Schema: public; Owner: intraday_user
--

ALTER TABLE ONLY public.equity_history
    ADD CONSTRAINT equity_history_pkey PRIMARY KEY (id);


--
-- Name: event_log event_log_event_id_key; Type: CONSTRAINT; Schema: public; Owner: intraday_user
--

ALTER TABLE ONLY public.event_log
    ADD CONSTRAINT event_log_event_id_key UNIQUE (event_id);


--
-- Name: event_log event_log_pkey; Type: CONSTRAINT; Schema: public; Owner: intraday_user
--

ALTER TABLE ONLY public.event_log
    ADD CONSTRAINT event_log_pkey PRIMARY KEY (id);


--
-- Name: order_rate_limit order_rate_limit_pkey; Type: CONSTRAINT; Schema: public; Owner: intraday_user
--

ALTER TABLE ONLY public.order_rate_limit
    ADD CONSTRAINT order_rate_limit_pkey PRIMARY KEY (id);


--
-- Name: positions positions_pkey; Type: CONSTRAINT; Schema: public; Owner: intraday_user
--

ALTER TABLE ONLY public.positions
    ADD CONSTRAINT positions_pkey PRIMARY KEY (id);


--
-- Name: risk_config risk_config_pkey; Type: CONSTRAINT; Schema: public; Owner: intraday_user
--

ALTER TABLE ONLY public.risk_config
    ADD CONSTRAINT risk_config_pkey PRIMARY KEY (id);


--
-- Name: trade_audit trade_audit_pkey; Type: CONSTRAINT; Schema: public; Owner: intraday_user
--

ALTER TABLE ONLY public.trade_audit
    ADD CONSTRAINT trade_audit_pkey PRIMARY KEY (id);


--
-- Name: trades trades_order_idempotency_key_key; Type: CONSTRAINT; Schema: public; Owner: intraday_user
--

ALTER TABLE ONLY public.trades
    ADD CONSTRAINT trades_order_idempotency_key_key UNIQUE (order_idempotency_key);


--
-- Name: trades trades_pkey; Type: CONSTRAINT; Schema: public; Owner: intraday_user
--

ALTER TABLE ONLY public.trades
    ADD CONSTRAINT trades_pkey PRIMARY KEY (id);


--
-- Name: positions unique_account_symbol; Type: CONSTRAINT; Schema: public; Owner: intraday_user
--

ALTER TABLE ONLY public.positions
    ADD CONSTRAINT unique_account_symbol UNIQUE (account_id, symbol);


--
-- Name: idx_risk_account_lookup; Type: INDEX; Schema: public; Owner: intraday_user
--

CREATE INDEX idx_risk_account_lookup ON public.risk_config USING btree (account_id);


--
-- Name: ix_positions_symbol; Type: INDEX; Schema: public; Owner: intraday_user
--

CREATE INDEX ix_positions_symbol ON public.positions USING btree (symbol);


--
-- Name: ix_trades_created_at; Type: INDEX; Schema: public; Owner: intraday_user
--

CREATE INDEX ix_trades_created_at ON public.trades USING btree (created_at);


--
-- Name: ix_trades_symbol; Type: INDEX; Schema: public; Owner: intraday_user
--

CREATE INDEX ix_trades_symbol ON public.trades USING btree (symbol);


--
-- Name: uq_risk_account; Type: INDEX; Schema: public; Owner: intraday_user
--

CREATE UNIQUE INDEX uq_risk_account ON public.risk_config USING btree (account_id);


--
-- Name: risk_config set_updated_at; Type: TRIGGER; Schema: public; Owner: intraday_user
--

CREATE TRIGGER set_updated_at BEFORE UPDATE ON public.risk_config FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: trade_audit fk_audit_account; Type: FK CONSTRAINT; Schema: public; Owner: intraday_user
--

ALTER TABLE ONLY public.trade_audit
    ADD CONSTRAINT fk_audit_account FOREIGN KEY (account_id) REFERENCES public.account(id);


--
-- Name: positions fk_positions_account; Type: FK CONSTRAINT; Schema: public; Owner: intraday_user
--

ALTER TABLE ONLY public.positions
    ADD CONSTRAINT fk_positions_account FOREIGN KEY (account_id) REFERENCES public.account(id);


--
-- Name: risk_config fk_risk_account; Type: FK CONSTRAINT; Schema: public; Owner: intraday_user
--

ALTER TABLE ONLY public.risk_config
    ADD CONSTRAINT fk_risk_account FOREIGN KEY (account_id) REFERENCES public.account(id);


--
-- Name: trades fk_trades_account; Type: FK CONSTRAINT; Schema: public; Owner: intraday_user
--

ALTER TABLE ONLY public.trades
    ADD CONSTRAINT fk_trades_account FOREIGN KEY (account_id) REFERENCES public.account(id);


--
-- PostgreSQL database dump complete
--

\unrestrict Fs19ThtIRBl7Qm64BOeyLZXO7UCREnPjmmDAZmx9vAdeOkqAgygqereVQjdmr7Q

