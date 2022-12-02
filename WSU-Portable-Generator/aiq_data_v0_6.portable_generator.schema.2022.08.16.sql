--
-- PostgreSQL database dump
--

-- Dumped from database version 12.5
-- Dumped by pg_dump version 12.6

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
-- Name: dataset_types; Type: TYPE; Schema: public; Owner: aiq_user
--

CREATE TYPE public.dataset_types AS ENUM (
    'train',
    'test',
    'live_train',
    'live_test'
);


ALTER TYPE public.dataset_types OWNER TO aiq_user;

--
-- Name: difficulty_type; Type: TYPE; Schema: public; Owner: aiq_user
--

CREATE TYPE public.difficulty_type AS ENUM (
    'easy',
    'medium',
    'hard'
);


ALTER TYPE public.difficulty_type OWNER TO aiq_user;

--
-- Name: experiment_types; Type: TYPE; Schema: public; Owner: aiq_user
--

CREATE TYPE public.experiment_types AS ENUM (
    'AIQ',
    'SAIL-ON',
    'SAIL-ON-SOTA'
);


ALTER TYPE public.experiment_types OWNER TO aiq_user;

--
-- Name: access_control_access_control_id_seq; Type: SEQUENCE; Schema: public; Owner: aiq_user
--

CREATE SEQUENCE public.access_control_access_control_id_seq
    START WITH 1
    INCREMENT BY 1
    MINVALUE 0
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.access_control_access_control_id_seq OWNER TO aiq_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: access_control; Type: TABLE; Schema: public; Owner: aiq_user
--

CREATE TABLE public.access_control (
    access_control_id integer DEFAULT nextval('public.access_control_access_control_id_seq'::regclass) NOT NULL,
    access_level text NOT NULL,
    access_group text NOT NULL,
    user_id integer NOT NULL,
    created_on timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.access_control OWNER TO aiq_user;

--
-- Name: access_group; Type: TABLE; Schema: public; Owner: aiq_user
--

CREATE TABLE public.access_group (
    name text NOT NULL,
    description text,
    created_on timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.access_group OWNER TO aiq_user;

--
-- Name: access_level; Type: TABLE; Schema: public; Owner: aiq_user
--

CREATE TABLE public.access_level (
    name text NOT NULL,
    description text,
    created_on timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.access_level OWNER TO aiq_user;

--
-- Name: data; Type: TABLE; Schema: public; Owner: aiq_user
--

CREATE TABLE public.data (
    data_id bigint NOT NULL,
    feature_vector jsonb NOT NULL,
    label jsonb NOT NULL,
    data_index bigint NOT NULL,
    episode_id bigint NOT NULL
);


ALTER TABLE public.data OWNER TO aiq_user;

--
-- Name: data_data_id_seq; Type: SEQUENCE; Schema: public; Owner: aiq_user
--

CREATE SEQUENCE public.data_data_id_seq
    START WITH 1
    INCREMENT BY 1
    MINVALUE 0
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.data_data_id_seq OWNER TO aiq_user;

--
-- Name: data_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: aiq_user
--

ALTER SEQUENCE public.data_data_id_seq OWNED BY public.data.data_id;


--
-- Name: dataset; Type: TABLE; Schema: public; Owner: aiq_user
--

CREATE TABLE public.dataset (
    dataset_id bigint NOT NULL,
    name text NOT NULL,
    version text NOT NULL,
    utc_created_on timestamp without time zone DEFAULT now() NOT NULL,
    description text,
    novelty smallint NOT NULL,
    seed numeric NOT NULL,
    domain_id integer NOT NULL,
    data_type public.dataset_types NOT NULL,
    episodes bigint,
    difficulty public.difficulty_type DEFAULT 'medium'::public.difficulty_type NOT NULL,
    locked_by uuid,
    locked_at timestamp without time zone DEFAULT now() NOT NULL,
    trial_novelty smallint
);


ALTER TABLE public.dataset OWNER TO aiq_user;

--
-- Name: dataset_dataset_id_seq; Type: SEQUENCE; Schema: public; Owner: aiq_user
--

CREATE SEQUENCE public.dataset_dataset_id_seq
    START WITH 1
    INCREMENT BY 1
    MINVALUE 0
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dataset_dataset_id_seq OWNER TO aiq_user;

--
-- Name: dataset_dataset_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: aiq_user
--

ALTER SEQUENCE public.dataset_dataset_id_seq OWNED BY public.dataset.dataset_id;


--
-- Name: domain_domain_id_seq; Type: SEQUENCE; Schema: public; Owner: aiq_user
--

CREATE SEQUENCE public.domain_domain_id_seq
    START WITH 1
    INCREMENT BY 1
    MINVALUE 0
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.domain_domain_id_seq OWNER TO aiq_user;

--
-- Name: domain; Type: TABLE; Schema: public; Owner: aiq_user
--

CREATE TABLE public.domain (
    domain_id integer DEFAULT nextval('public.domain_domain_id_seq'::regclass) NOT NULL,
    name text NOT NULL,
    description text,
    utc_created_on timestamp without time zone DEFAULT now() NOT NULL,
    utc_updated_on timestamp without time zone
);


ALTER TABLE public.domain OWNER TO aiq_user;

--
-- Name: episode_episode_id_seq; Type: SEQUENCE; Schema: public; Owner: aiq_user
--

CREATE SEQUENCE public.episode_episode_id_seq
    START WITH 1
    INCREMENT BY 1
    MINVALUE 0
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.episode_episode_id_seq OWNER TO aiq_user;

--
-- Name: episode; Type: TABLE; Schema: public; Owner: aiq_user
--

CREATE TABLE public.episode (
    episode_id bigint DEFAULT nextval('public.episode_episode_id_seq'::regclass) NOT NULL,
    dataset_id bigint NOT NULL,
    size integer,
    episode_index bigint,
    seed numeric
);


ALTER TABLE public.episode OWNER TO aiq_user;

--
-- Name: experiment_domain; Type: TABLE; Schema: public; Owner: aiq_user
--

CREATE TABLE public.experiment_domain (
    model_experiment_id bigint NOT NULL,
    domain_id integer NOT NULL
);


ALTER TABLE public.experiment_domain OWNER TO aiq_user;

--
-- Name: experiment_log; Type: TABLE; Schema: public; Owner: aiq_user
--

CREATE TABLE public.experiment_log (
    experiment_log_id bigint NOT NULL,
    model_experiment_id bigint NOT NULL,
    utc_stamp timestamp without time zone DEFAULT now() NOT NULL,
    action text NOT NULL,
    message text,
    object jsonb,
    experiment_trial_id bigint
);


ALTER TABLE public.experiment_log OWNER TO aiq_user;

--
-- Name: experiment_log_experiment_log_id_seq; Type: SEQUENCE; Schema: public; Owner: aiq_user
--

CREATE SEQUENCE public.experiment_log_experiment_log_id_seq
    START WITH 1
    INCREMENT BY 1
    MINVALUE 0
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.experiment_log_experiment_log_id_seq OWNER TO aiq_user;

--
-- Name: experiment_log_experiment_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: aiq_user
--

ALTER SEQUENCE public.experiment_log_experiment_log_id_seq OWNED BY public.experiment_log.experiment_log_id;


--
-- Name: experiment_trial_experiment_trial_id_seq; Type: SEQUENCE; Schema: public; Owner: aiq_user
--

CREATE SEQUENCE public.experiment_trial_experiment_trial_id_seq
    START WITH 1
    INCREMENT BY 1
    MINVALUE 0
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.experiment_trial_experiment_trial_id_seq OWNER TO aiq_user;

--
-- Name: experiment_trial; Type: TABLE; Schema: public; Owner: aiq_user
--

CREATE TABLE public.experiment_trial (
    experiment_trial_id bigint DEFAULT nextval('public.experiment_trial_experiment_trial_id_seq'::regclass) NOT NULL,
    model_experiment_id bigint NOT NULL,
    trial integer DEFAULT 0 NOT NULL,
    is_active boolean DEFAULT false NOT NULL,
    novelty integer DEFAULT 0 NOT NULL,
    novelty_visibility integer DEFAULT 0 NOT NULL,
    difficulty public.difficulty_type DEFAULT 'medium'::public.difficulty_type NOT NULL,
    novelty_description jsonb NOT NULL,
    utc_stamp_started timestamp without time zone,
    utc_stamp_ended timestamp without time zone,
    locked_by uuid,
    is_complete boolean DEFAULT false NOT NULL,
    utc_last_updated timestamp without time zone,
    hint_level smallint DEFAULT -1 NOT NULL,
    filename text,
    is_data_imported boolean DEFAULT false NOT NULL
);


ALTER TABLE public.experiment_trial OWNER TO aiq_user;

--
-- Name: model; Type: TABLE; Schema: public; Owner: aiq_user
--

CREATE TABLE public.model (
    model_id integer NOT NULL,
    user_id integer NOT NULL,
    name text NOT NULL,
    description text,
    organization_id integer NOT NULL,
    share_with_organization boolean DEFAULT false NOT NULL
);


ALTER TABLE public.model OWNER TO aiq_user;

--
-- Name: model_experiment_model_experiment_id_seq; Type: SEQUENCE; Schema: public; Owner: aiq_user
--

CREATE SEQUENCE public.model_experiment_model_experiment_id_seq
    START WITH 1
    INCREMENT BY 1
    MINVALUE 0
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.model_experiment_model_experiment_id_seq OWNER TO aiq_user;

--
-- Name: model_experiment; Type: TABLE; Schema: public; Owner: aiq_user
--

CREATE TABLE public.model_experiment (
    model_experiment_id bigint DEFAULT nextval('public.model_experiment_model_experiment_id_seq'::regclass) NOT NULL,
    model_id integer NOT NULL,
    novelty smallint NOT NULL,
    seed numeric NOT NULL,
    git_version text NOT NULL,
    utc_stamp_started timestamp without time zone DEFAULT now() NOT NULL,
    utc_stamp_ended timestamp without time zone,
    description text,
    secret uuid NOT NULL,
    novelty_visibility integer DEFAULT 0 NOT NULL,
    experiment_type public.experiment_types DEFAULT 'AIQ'::public.experiment_types NOT NULL,
    sota_experiment_id bigint,
    is_active boolean DEFAULT true NOT NULL,
    experiment_json json,
    vhost text NOT NULL,
    phase text DEFAULT '3' NOT NULL
);


ALTER TABLE public.model_experiment OWNER TO aiq_user;

--
-- Name: model_model_id_seq; Type: SEQUENCE; Schema: public; Owner: aiq_user
--

CREATE SEQUENCE public.model_model_id_seq
    START WITH 1
    INCREMENT BY 1
    MINVALUE 0
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.model_model_id_seq OWNER TO aiq_user;

--
-- Name: model_model_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: aiq_user
--

ALTER SEQUENCE public.model_model_id_seq OWNED BY public.model.model_id;


--
-- Name: organization_organization_id_seq; Type: SEQUENCE; Schema: public; Owner: aiq_user
--

CREATE SEQUENCE public.organization_organization_id_seq
    START WITH 1
    INCREMENT BY 1
    MINVALUE 0
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.organization_organization_id_seq OWNER TO aiq_user;

--
-- Name: organization; Type: TABLE; Schema: public; Owner: aiq_user
--

CREATE TABLE public.organization (
    organization_id integer DEFAULT nextval('public.organization_organization_id_seq'::regclass) NOT NULL,
    name text NOT NULL,
    utc_created_on timestamp without time zone DEFAULT now() NOT NULL,
    share_model_by_default boolean DEFAULT false NOT NULL
);


ALTER TABLE public.organization OWNER TO aiq_user;

--
-- Name: organization_users; Type: TABLE; Schema: public; Owner: aiq_user
--

CREATE TABLE public.organization_users (
    organization_id integer NOT NULL,
    user_id integer NOT NULL,
    organization_owner boolean DEFAULT false NOT NULL,
    utc_created_on timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.organization_users OWNER TO aiq_user;

--
-- Name: sota_experiments_sota_experiments_id_seq; Type: SEQUENCE; Schema: public; Owner: aiq_user
--

CREATE SEQUENCE public.sota_experiments_sota_experiments_id_seq
    START WITH 1
    INCREMENT BY 1
    MINVALUE 0
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sota_experiments_sota_experiments_id_seq OWNER TO aiq_user;

--
-- Name: sota_experiments; Type: TABLE; Schema: public; Owner: aiq_user
--

CREATE TABLE public.sota_experiments (
    sota_experiments_id bigint DEFAULT nextval('public.sota_experiments_sota_experiments_id_seq'::regclass) NOT NULL,
    experiment_json jsonb NOT NULL,
    utc_created_on timestamp without time zone DEFAULT now() NOT NULL,
    domain_id integer NOT NULL,
    version text NOT NULL,
    claimed_id uuid,
    model_experiment_id bigint NOT NULL,
    vhost text NOT NULL
);


ALTER TABLE public.sota_experiments OWNER TO aiq_user;

--
-- Name: test_instance; Type: TABLE; Schema: public; Owner: aiq_user
--

CREATE TABLE public.test_instance (
    test_instance_id bigint NOT NULL,
    data_id bigint NOT NULL,
    utc_stamp_sent timestamp without time zone DEFAULT now() NOT NULL,
    utc_stamp_received timestamp without time zone,
    utc_remote_stamp_arrived timestamp without time zone,
    utc_remote_stamp_replied timestamp without time zone,
    trial_episode_id bigint NOT NULL
);


ALTER TABLE public.test_instance OWNER TO aiq_user;

--
-- Name: test_instance_test_instance_id_seq; Type: SEQUENCE; Schema: public; Owner: aiq_user
--

CREATE SEQUENCE public.test_instance_test_instance_id_seq
    START WITH 1
    INCREMENT BY 1
    MINVALUE 0
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.test_instance_test_instance_id_seq OWNER TO aiq_user;

--
-- Name: test_instance_test_instance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: aiq_user
--

ALTER SEQUENCE public.test_instance_test_instance_id_seq OWNED BY public.test_instance.test_instance_id;


--
-- Name: test_label; Type: TABLE; Schema: public; Owner: aiq_user
--

CREATE TABLE public.test_label (
    test_label_id bigint NOT NULL,
    label_prediction jsonb NOT NULL,
    test_instance_id bigint NOT NULL,
    performance numeric,
    feedback jsonb
);


ALTER TABLE public.test_label OWNER TO aiq_user;

--
-- Name: test_label_test_label_id_seq; Type: SEQUENCE; Schema: public; Owner: aiq_user
--

CREATE SEQUENCE public.test_label_test_label_id_seq
    START WITH 1
    INCREMENT BY 1
    MINVALUE 0
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.test_label_test_label_id_seq OWNER TO aiq_user;

--
-- Name: test_label_test_label_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: aiq_user
--

ALTER SEQUENCE public.test_label_test_label_id_seq OWNED BY public.test_label.test_label_id;


--
-- Name: trial_episode_trial_episode_id_seq; Type: SEQUENCE; Schema: public; Owner: aiq_user
--

CREATE SEQUENCE public.trial_episode_trial_episode_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.trial_episode_trial_episode_id_seq OWNER TO aiq_user;

--
-- Name: trial_episode; Type: TABLE; Schema: public; Owner: aiq_user
--

CREATE TABLE public.trial_episode (
    trial_episode_id bigint DEFAULT nextval('public.trial_episode_trial_episode_id_seq'::regclass) NOT NULL,
    experiment_trial_id bigint NOT NULL,
    episode_index integer NOT NULL,
    novelty smallint,
    novelty_initiated boolean,
    performance numeric,
    novelty_probability numeric,
    novelty_characterization jsonb,
    utc_stamp_started timestamp without time zone,
    utc_stamp_ended timestamp without time zone,
    novelty_threshold numeric,
    budget_active boolean DEFAULT false NOT NULL,
    hint_json jsonb,
    hint_level smallint DEFAULT -1 NOT NULL
);


ALTER TABLE public.trial_episode OWNER TO aiq_user;

--
-- Name: users; Type: TABLE; Schema: public; Owner: aiq_user
--

CREATE TABLE public.users (
    user_id integer NOT NULL,
    username text NOT NULL,
    password text NOT NULL,
    secret uuid NOT NULL,
    confirmed_at timestamp without time zone,
    is_active boolean DEFAULT false NOT NULL,
    first_name text DEFAULT 'FirstName'::text NOT NULL,
    last_name text DEFAULT 'LastName'::text NOT NULL,
    login_count integer DEFAULT 0 NOT NULL,
    last_login_ip text,
    last_seen timestamp without time zone
);


ALTER TABLE public.users OWNER TO aiq_user;

--
-- Name: user_available_models; Type: VIEW; Schema: public; Owner: aiq_user
--

CREATE VIEW public.user_available_models AS
 SELECT users.user_id,
    users.username,
    organization.organization_id,
    organization.name AS organization_name,
    model.model_id,
    model.name AS model_name,
    model.share_with_organization
   FROM (((public.users
     JOIN public.organization_users ON ((users.user_id = organization_users.user_id)))
     JOIN public.organization ON ((organization_users.organization_id = organization.organization_id)))
     JOIN public.model ON ((organization.organization_id = model.organization_id)))
  ORDER BY users.user_id, organization.organization_id, model.model_id;


ALTER TABLE public.user_available_models OWNER TO aiq_user;

--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: aiq_user
--

CREATE SEQUENCE public.users_user_id_seq
    START WITH 1
    INCREMENT BY 1
    MINVALUE 0
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_user_id_seq OWNER TO aiq_user;

--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: aiq_user
--

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;


--
-- Name: website_log; Type: TABLE; Schema: public; Owner: aiq_user
--

CREATE TABLE public.website_log (
    website_log_id integer NOT NULL,
    stamp timestamp without time zone DEFAULT now() NOT NULL,
    level integer DEFAULT 1 NOT NULL,
    message text NOT NULL,
    user_id integer
);


ALTER TABLE public.website_log OWNER TO aiq_user;

--
-- Name: website_log_website_log_id_seq; Type: SEQUENCE; Schema: public; Owner: aiq_user
--

CREATE SEQUENCE public.website_log_website_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.website_log_website_log_id_seq OWNER TO aiq_user;

--
-- Name: website_log_website_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: aiq_user
--

ALTER SEQUENCE public.website_log_website_log_id_seq OWNED BY public.website_log.website_log_id;


--
-- Name: data data_id; Type: DEFAULT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.data ALTER COLUMN data_id SET DEFAULT nextval('public.data_data_id_seq'::regclass);


--
-- Name: dataset dataset_id; Type: DEFAULT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.dataset ALTER COLUMN dataset_id SET DEFAULT nextval('public.dataset_dataset_id_seq'::regclass);


--
-- Name: experiment_log experiment_log_id; Type: DEFAULT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.experiment_log ALTER COLUMN experiment_log_id SET DEFAULT nextval('public.experiment_log_experiment_log_id_seq'::regclass);


--
-- Name: model model_id; Type: DEFAULT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.model ALTER COLUMN model_id SET DEFAULT nextval('public.model_model_id_seq'::regclass);


--
-- Name: test_instance test_instance_id; Type: DEFAULT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.test_instance ALTER COLUMN test_instance_id SET DEFAULT nextval('public.test_instance_test_instance_id_seq'::regclass);


--
-- Name: test_label test_label_id; Type: DEFAULT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.test_label ALTER COLUMN test_label_id SET DEFAULT nextval('public.test_label_test_label_id_seq'::regclass);


--
-- Name: users user_id; Type: DEFAULT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.users ALTER COLUMN user_id SET DEFAULT nextval('public.users_user_id_seq'::regclass);


--
-- Name: website_log website_log_id; Type: DEFAULT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.website_log ALTER COLUMN website_log_id SET DEFAULT nextval('public.website_log_website_log_id_seq'::regclass);


--
-- Name: access_control access_control_pkey; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.access_control
    ADD CONSTRAINT access_control_pkey PRIMARY KEY (access_control_id);


--
-- Name: access_group access_group_pkey; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.access_group
    ADD CONSTRAINT access_group_pkey PRIMARY KEY (name);


--
-- Name: access_level access_level_pkey; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.access_level
    ADD CONSTRAINT access_level_pkey PRIMARY KEY (name);


--
-- Name: data data_episode_id_data_index_key; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.data
    ADD CONSTRAINT data_episode_id_data_index_key UNIQUE (episode_id, data_index);


--
-- Name: data data_pkey; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.data
    ADD CONSTRAINT data_pkey PRIMARY KEY (data_id);


--
-- Name: dataset dataset_domain_novelty_type_difficulty_version_trialnovelty_key; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.dataset
    ADD CONSTRAINT dataset_domain_novelty_type_difficulty_version_trialnovelty_key UNIQUE (version, novelty, domain_id, data_type, difficulty, trial_novelty);


--
-- Name: dataset dataset_pkey; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.dataset
    ADD CONSTRAINT dataset_pkey PRIMARY KEY (dataset_id);


--
-- Name: domain domain_name_key; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.domain
    ADD CONSTRAINT domain_name_key UNIQUE (name);


--
-- Name: domain domain_pkey; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.domain
    ADD CONSTRAINT domain_pkey PRIMARY KEY (domain_id);


--
-- Name: episode episode_dataset_id_episode_index_key; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.episode
    ADD CONSTRAINT episode_dataset_id_episode_index_key UNIQUE (dataset_id, episode_index);


--
-- Name: episode episode_pkey; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.episode
    ADD CONSTRAINT episode_pkey PRIMARY KEY (episode_id);


--
-- Name: experiment_domain experiment_domain_pkey; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.experiment_domain
    ADD CONSTRAINT experiment_domain_pkey PRIMARY KEY (model_experiment_id, domain_id);


--
-- Name: experiment_log experiment_log_pkey; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.experiment_log
    ADD CONSTRAINT experiment_log_pkey PRIMARY KEY (experiment_log_id);


--
-- Name: experiment_trial experiment_trial_mod_ex_id_trial_nov_nov_vis_diff_hint; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.experiment_trial
    ADD CONSTRAINT experiment_trial_mod_ex_id_trial_nov_nov_vis_diff_hint UNIQUE (model_experiment_id, trial, novelty, novelty_visibility, difficulty, hint_level);


--
-- Name: experiment_trial experiment_trial_pkey; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.experiment_trial
    ADD CONSTRAINT experiment_trial_pkey PRIMARY KEY (experiment_trial_id);


--
-- Name: model_experiment model_experiment_pkey; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.model_experiment
    ADD CONSTRAINT model_experiment_pkey PRIMARY KEY (model_experiment_id);


--
-- Name: model model_pkey; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.model
    ADD CONSTRAINT model_pkey PRIMARY KEY (model_id);


--
-- Name: model model_user_id_name_unique_key; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.model
    ADD CONSTRAINT model_user_id_name_unique_key UNIQUE (user_id, name);


--
-- Name: organization organization_name_key; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.organization
    ADD CONSTRAINT organization_name_key UNIQUE (name);


--
-- Name: organization organization_pkey; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.organization
    ADD CONSTRAINT organization_pkey PRIMARY KEY (organization_id);


--
-- Name: organization_users organization_users_pkey; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.organization_users
    ADD CONSTRAINT organization_users_pkey PRIMARY KEY (organization_id, user_id);


--
-- Name: sota_experiments sota_experiments_pkey; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.sota_experiments
    ADD CONSTRAINT sota_experiments_pkey PRIMARY KEY (sota_experiments_id);


--
-- Name: test_instance test_instance_pkey; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.test_instance
    ADD CONSTRAINT test_instance_pkey PRIMARY KEY (test_instance_id);


--
-- Name: test_label test_label_pkey; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.test_label
    ADD CONSTRAINT test_label_pkey PRIMARY KEY (test_label_id);


--
-- Name: trial_episode trial_episode_pkey; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.trial_episode
    ADD CONSTRAINT trial_episode_pkey PRIMARY KEY (trial_episode_id);


--
-- Name: trial_episode trial_episode_trial_episode_id_episode_index_key; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.trial_episode
    ADD CONSTRAINT trial_episode_trial_episode_id_episode_index_key UNIQUE (experiment_trial_id, episode_index);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: users users_secret_unique_key; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_secret_unique_key UNIQUE (secret);


--
-- Name: users users_username_unique_key; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_unique_key UNIQUE (username);


--
-- Name: website_log website_log_pkey; Type: CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.website_log
    ADD CONSTRAINT website_log_pkey PRIMARY KEY (website_log_id);


--
-- Name: access_control_access_group_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX access_control_access_group_index ON public.access_control USING btree (access_group);


--
-- Name: access_control_access_level_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX access_control_access_level_index ON public.access_control USING btree (access_level);


--
-- Name: access_control_user_id_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX access_control_user_id_index ON public.access_control USING btree (user_id);


--
-- Name: data_data_id_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX data_data_id_index ON public.data USING btree (data_id);


--
-- Name: data_data_index_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX data_data_index_index ON public.data USING btree (data_index);


--
-- Name: data_episode_id_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX data_episode_id_index ON public.data USING btree (episode_id);


--
-- Name: data_label_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX data_label_index ON public.data USING btree (label);


--
-- Name: dataset_data_type_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX dataset_data_type_index ON public.dataset USING btree (data_type);


--
-- Name: dataset_difficulty_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX dataset_difficulty_index ON public.dataset USING btree (difficulty);


--
-- Name: dataset_domain_id_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX dataset_domain_id_index ON public.dataset USING btree (domain_id);


--
-- Name: dataset_name_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX dataset_name_index ON public.dataset USING btree (name);


--
-- Name: dataset_novelty_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX dataset_novelty_index ON public.dataset USING btree (novelty);


--
-- Name: dataset_utc_created_on_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX dataset_utc_created_on_index ON public.dataset USING btree (utc_created_on);


--
-- Name: dataset_version_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX dataset_version_index ON public.dataset USING btree (version);


--
-- Name: domain_name_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX domain_name_index ON public.domain USING btree (name);


--
-- Name: episode_dataset_id_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX episode_dataset_id_index ON public.episode USING btree (dataset_id);


--
-- Name: episode_episode_index_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX episode_episode_index_index ON public.episode USING btree (episode_index);


--
-- Name: episode_seed_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX episode_seed_index ON public.episode USING btree (seed);


--
-- Name: experiment_log_action_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX experiment_log_action_index ON public.experiment_log USING btree (action);


--
-- Name: experiment_log_model_experiment_id_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX experiment_log_model_experiment_id_index ON public.experiment_log USING btree (model_experiment_id);


--
-- Name: experiment_log_utc_stamp_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX experiment_log_utc_stamp_index ON public.experiment_log USING btree (utc_stamp);


--
-- Name: experiment_trial_difficulty_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX experiment_trial_difficulty_index ON public.experiment_trial USING btree (difficulty);


--
-- Name: experiment_trial_is_active_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX experiment_trial_is_active_index ON public.experiment_trial USING btree (is_active);


--
-- Name: experiment_trial_is_complete_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX experiment_trial_is_complete_index ON public.experiment_trial USING btree (is_complete);


--
-- Name: experiment_trial_locked_by_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX experiment_trial_locked_by_index ON public.experiment_trial USING btree (locked_by NULLS FIRST);


--
-- Name: experiment_trial_model_experiment_id_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX experiment_trial_model_experiment_id_index ON public.experiment_trial USING btree (model_experiment_id);


--
-- Name: experiment_trial_novelty_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX experiment_trial_novelty_index ON public.experiment_trial USING btree (novelty);


--
-- Name: experiment_trial_novelty_visibility_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX experiment_trial_novelty_visibility_index ON public.experiment_trial USING btree (novelty_visibility);


--
-- Name: experiment_trial_trial_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX experiment_trial_trial_index ON public.experiment_trial USING btree (trial);


--
-- Name: experiment_trial_utc_last_updated_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX experiment_trial_utc_last_updated_index ON public.experiment_trial USING btree (utc_last_updated);


--
-- Name: experiment_trial_hint_level_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX experiment_trial_hint_level_index ON public.experiment_trial USING btree (hint_level);


--
-- Name: experiment_trial_filename_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX experiment_trial_filename_index ON public.experiment_trial USING btree (filename);


--
-- Name: experiment_trial_is_data_imported_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX experiment_trial_is_data_imported_index ON public.experiment_trial USING btree (is_data_imported);


--
-- Name: model_experiment_git_version_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX model_experiment_git_version_index ON public.model_experiment USING btree (git_version);


--
-- Name: model_experiment_is_active_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX model_experiment_is_active_index ON public.model_experiment USING btree (is_active);


--
-- Name: model_experiment_model_id_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX model_experiment_model_id_index ON public.model_experiment USING btree (model_id);


--
-- Name: model_experiment_novelty_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX model_experiment_novelty_index ON public.model_experiment USING btree (novelty);


--
-- Name: model_experiment_secret_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX model_experiment_secret_index ON public.model_experiment USING btree (secret);


--
-- Name: model_experiment_seed_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX model_experiment_seed_index ON public.model_experiment USING btree (seed);


--
-- Name: model_experiment_sota_experiment_id_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX model_experiment_sota_experiment_id_index ON public.model_experiment USING btree (sota_experiment_id);


--
-- Name: model_experiment_utc_stamp_ended_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX model_experiment_utc_stamp_ended_index ON public.model_experiment USING btree (utc_stamp_ended);


--
-- Name: model_experiment_utc_stamp_started_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX model_experiment_utc_stamp_started_index ON public.model_experiment USING btree (utc_stamp_started);


--
-- Name: model_experiment_vhost_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX model_experiment_vhost_index ON public.model_experiment USING btree (vhost);


--
-- Name: model_experiment_phase_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX model_experiment_phase_index ON public.model_experiment USING btree (phase);


--
-- Name: model_name_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX model_name_index ON public.model USING btree (name);


--
-- Name: model_organization_id_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX model_organization_id_index ON public.model USING btree (organization_id);


--
-- Name: model_user_id_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX model_user_id_index ON public.model USING btree (user_id);


--
-- Name: sota_experiments_domain_id_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX sota_experiments_domain_id_index ON public.sota_experiments USING btree (domain_id);


--
-- Name: sota_experiments_utc_created_on_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX sota_experiments_utc_created_on_index ON public.sota_experiments USING btree (utc_created_on DESC NULLS LAST);


--
-- Name: sota_experiments_version_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX sota_experiments_version_index ON public.sota_experiments USING btree (version);


--
-- Name: test_instance_data_id_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX test_instance_data_id_index ON public.test_instance USING btree (data_id);


--
-- Name: test_instance_trial_episode_id_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX test_instance_trial_episode_id_index ON public.test_instance USING btree (trial_episode_id);


--
-- Name: test_instance_utc_stamp_received_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX test_instance_utc_stamp_received_index ON public.test_instance USING btree (utc_stamp_received);


--
-- Name: test_instance_utc_stamp_sent_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX test_instance_utc_stamp_sent_index ON public.test_instance USING btree (utc_stamp_sent);


--
-- Name: test_label_test_instance_id_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX test_label_test_instance_id_index ON public.test_label USING btree (test_instance_id);


--
-- Name: trial_episode_episode_index_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX trial_episode_episode_index_index ON public.trial_episode USING btree (episode_index);


--
-- Name: trial_episode_experiment_trial_id_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX trial_episode_experiment_trial_id_index ON public.trial_episode USING btree (experiment_trial_id);


--
-- Name: trial_episode_novelty_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX trial_episode_novelty_index ON public.trial_episode USING btree (novelty);


--
-- Name: users_secret_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE UNIQUE INDEX users_secret_index ON public.users USING btree (secret);


--
-- Name: users_username_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX users_username_index ON public.users USING btree (username);


--
-- Name: website_log_stamp_index; Type: INDEX; Schema: public; Owner: aiq_user
--

CREATE INDEX website_log_stamp_index ON public.website_log USING btree (stamp);


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: aiq_user
--

COPY public.users (user_id, username, password, secret, confirmed_at, is_active, first_name, last_name, login_count, last_login_ip, last_seen) FROM stdin;
5	demo@example.com	5	2d51a267-2cbd-4346-985d-a63bdb947a00	\N	f	FirstName	LastName	0	\N	\N
\.


--
-- Data for Name: domain; Type: TABLE DATA; Schema: public; Owner: aiq_user
--

COPY public.domain (domain_id, name, description, utc_created_on, utc_updated_on) FROM stdin;
1	cartpole	\N	2020-09-15 22:27:42.145048	\N
2	vizdoom	\N	2020-09-15 22:27:53.59381	\N
3	smartenv	\N	2020-09-15 22:28:01.088925	\N
\.


--
-- Data for Name: organization; Type: TABLE DATA; Schema: public; Owner: aiq_user
--

COPY public.organization (organization_id, name, utc_created_on, share_model_by_default) FROM stdin;
1	WSU	2021-01-22 00:20:16.60736	f
3	DemoOrg	2021-01-22 00:20:51.397747	f
5	UCCS	2021-01-22 00:21:19.2917	f
\.


--
-- Data for Name: model; Type: TABLE DATA; Schema: public; Owner: aiq_user
--

COPY public.model (model_id, user_id, name, description, organization_id, share_with_organization) FROM stdin;
26	5	DemoAgent42	\N	3	f
\.


--
-- Name: access_control access_control_access_group_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.access_control
    ADD CONSTRAINT access_control_access_group_fkey FOREIGN KEY (access_group) REFERENCES public.access_group(name) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: access_control access_control_access_level_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.access_control
    ADD CONSTRAINT access_control_access_level_fkey FOREIGN KEY (access_level) REFERENCES public.access_level(name) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: access_control access_control_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.access_control
    ADD CONSTRAINT access_control_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: data data_episode_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.data
    ADD CONSTRAINT data_episode_id_fkey FOREIGN KEY (episode_id) REFERENCES public.episode(episode_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: dataset dataset_domain_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.dataset
    ADD CONSTRAINT dataset_domain_id_fkey FOREIGN KEY (domain_id) REFERENCES public.domain(domain_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: episode episode_dataset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.episode
    ADD CONSTRAINT episode_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES public.dataset(dataset_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: experiment_domain experiment_domain_domain_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.experiment_domain
    ADD CONSTRAINT experiment_domain_domain_id_fkey FOREIGN KEY (domain_id) REFERENCES public.domain(domain_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: experiment_domain experiment_domain_model_experiment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.experiment_domain
    ADD CONSTRAINT experiment_domain_model_experiment_id_fkey FOREIGN KEY (model_experiment_id) REFERENCES public.model_experiment(model_experiment_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: experiment_log experiment_log_experiment_trial_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.experiment_log
    ADD CONSTRAINT experiment_log_experiment_trial_id_fkey FOREIGN KEY (experiment_trial_id) REFERENCES public.experiment_trial(experiment_trial_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: experiment_log experiment_log_model_experiment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.experiment_log
    ADD CONSTRAINT experiment_log_model_experiment_id_fkey FOREIGN KEY (model_experiment_id) REFERENCES public.model_experiment(model_experiment_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: experiment_trial experiment_trial_model_experiment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.experiment_trial
    ADD CONSTRAINT experiment_trial_model_experiment_id_fkey FOREIGN KEY (model_experiment_id) REFERENCES public.model_experiment(model_experiment_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: model_experiment model_experiment_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.model_experiment
    ADD CONSTRAINT model_experiment_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.model(model_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: model_experiment model_experiment_sota_experiment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.model_experiment
    ADD CONSTRAINT model_experiment_sota_experiment_id_fkey FOREIGN KEY (sota_experiment_id) REFERENCES public.model_experiment(model_experiment_id);


--
-- Name: model model_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.model
    ADD CONSTRAINT model_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organization(organization_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: model model_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.model
    ADD CONSTRAINT model_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) MATCH FULL ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: organization_users organization_users_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.organization_users
    ADD CONSTRAINT organization_users_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organization(organization_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: organization_users organization_users_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.organization_users
    ADD CONSTRAINT organization_users_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: sota_experiments sota_experiments_domain_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.sota_experiments
    ADD CONSTRAINT sota_experiments_domain_id_fkey FOREIGN KEY (domain_id) REFERENCES public.domain(domain_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: sota_experiments sota_experiments_model_experiment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.sota_experiments
    ADD CONSTRAINT sota_experiments_model_experiment_id_fkey FOREIGN KEY (model_experiment_id) REFERENCES public.model_experiment(model_experiment_id);


--
-- Name: test_instance test_instance_data_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.test_instance
    ADD CONSTRAINT test_instance_data_id_fkey FOREIGN KEY (data_id) REFERENCES public.data(data_id) MATCH FULL ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: test_instance test_instance_trial_episode_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.test_instance
    ADD CONSTRAINT test_instance_trial_episode_id_fkey FOREIGN KEY (trial_episode_id) REFERENCES public.trial_episode(trial_episode_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: test_label test_label_test_instance_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.test_label
    ADD CONSTRAINT test_label_test_instance_id_fkey FOREIGN KEY (test_instance_id) REFERENCES public.test_instance(test_instance_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: trial_episode trial_episode_experiment_trial_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.trial_episode
    ADD CONSTRAINT trial_episode_experiment_trial_id_fkey FOREIGN KEY (experiment_trial_id) REFERENCES public.experiment_trial(experiment_trial_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: website_log website_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiq_user
--

ALTER TABLE ONLY public.website_log
    ADD CONSTRAINT website_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: users_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: aiq_user
--

SELECT pg_catalog.setval('public.users_user_id_seq', 8, true);


--
-- Name: model_model_id_seq; Type: SEQUENCE SET; Schema: public; Owner: aiq_user
--

SELECT pg_catalog.setval('public.model_model_id_seq', 44, true);




--
-- PostgreSQL database dump complete
--

